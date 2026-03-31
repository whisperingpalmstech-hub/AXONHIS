"""
Auth services – enterprise authentication with RBAC, session tracking, account lockout.

Business rules:
- Account locks after 5 failed login attempts for 30 minutes
- Refresh tokens are hashed and stored in device_sessions
- Token revocation works by deactivating the device session
- Permission checks traverse user → user_roles → role → role_permissions → permission
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.auth.models import (
    DeviceSession,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
    UserStatus,
)
from app.core.auth.schemas import UserCreate

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except ValueError:
        return False


def _hash_token(token: str) -> str:
    """SHA-256 hash of refresh token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def _create_jwt(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    payload["iat"] = datetime.now(timezone.utc)
    payload["jti"] = uuid.uuid4().hex
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


class AuthService:
    """Core authentication and authorization service."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── User Management ───────────────────────────────────────────────────

    async def create_user(self, data: UserCreate, org_id: uuid.UUID | None = None) -> User:
        """Create a new user with optional role assignments, scoped to org_id."""
        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            org_id=org_id,
        )
        self.db.add(user)
        await self.db.flush()

        # Assign roles
        for role_id in data.role_ids:
            self.db.add(UserRole(user_id=user.id, role_id=role_id))

        await self.db.flush()
        return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role)
                .selectinload(Role.role_permissions).selectinload(RolePermission.permission)
            )
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User)
            .where(User.email == email)
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role)
                .selectinload(Role.role_permissions).selectinload(RolePermission.permission)
            )
        )
        return result.scalar_one_or_none()

    async def list_users(self, skip: int = 0, limit: int = 20, org_id: uuid.UUID | None = None) -> tuple[list[User], int]:
        count_stmt = select(func.count(User.id))
        list_stmt = select(User).options(
            selectinload(User.user_roles).selectinload(UserRole.role)
            .selectinload(Role.role_permissions).selectinload(RolePermission.permission)
        )
        if org_id:
            count_stmt = count_stmt.where(User.org_id == org_id)
            list_stmt = list_stmt.where(User.org_id == org_id)
        count = (await self.db.execute(count_stmt)).scalar_one()
        result = await self.db.execute(
            list_stmt.offset(skip).limit(limit).order_by(User.created_at.desc())
        )
        return list(result.scalars().all()), count

    async def update_user(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        await self.db.flush()
        return user

    # ── Authentication ────────────────────────────────────────────────────

    async def authenticate(
        self, email: str, password: str, ip_address: str | None = None,
        device_name: str | None = None, device_type: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User | None, str | None]:
        """
        Authenticate user credentials.
        Returns (user, error_message). On success error_message is None.
        Handles account lockout and failed attempt tracking.
        """
        user = await self.get_user_by_email(email)
        if user is None:
            return None, "Invalid email or password"

        # Check lockout
        if user.is_locked:
            return None, "Account is locked due to too many failed attempts"

        # Clear expired lockout
        if user.status == UserStatus.LOCKED and user.locked_until:
            if user.locked_until <= datetime.now(timezone.utc):
                user.status = UserStatus.ACTIVE
                user.failed_login_attempts = 0
                user.locked_until = None

        if not user.is_active:
            return None, "Account is not active"

        # Verify password
        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.status = UserStatus.LOCKED
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=LOCKOUT_DURATION_MINUTES
                )
            await self.db.flush()
            return None, "Invalid email or password"

        # Successful login — reset counters
        user.failed_login_attempts = 0
        user.status = UserStatus.ACTIVE
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()
        return user, None

    # ── Token Management ──────────────────────────────────────────────────

    def create_access_token(self, user: User) -> str:
        """Create JWT access token with user roles and permissions embedded."""
        roles = [ur.role.name for ur in user.user_roles] if user.user_roles else []
        permissions: list[str] = []
        for ur in (user.user_roles or []):
            for rp in (ur.role.role_permissions or []):
                if rp.permission.code not in permissions:
                    permissions.append(rp.permission.code)

        return _create_jwt(
            {
                "sub": str(user.id),
                "email": user.email,
                "org_id": str(user.org_id) if user.org_id else None,
                "roles": roles,
                "permissions": permissions,
                "type": "access",
            },
            timedelta(minutes=settings.access_token_expire_minutes),
        )

    def create_refresh_token(self, user: User) -> str:
        return _create_jwt(
            {"sub": str(user.id), "type": "refresh"},
            timedelta(days=settings.refresh_token_expire_days),
        )

    async def create_session(
        self, user: User, refresh_token: str,
        ip_address: str | None = None, device_name: str | None = None,
        device_type: str | None = None, user_agent: str | None = None,
    ) -> DeviceSession:
        """Store a hashed refresh token in a device session."""
        session = DeviceSession(
            user_id=user.id,
            refresh_token_hash=_hash_token(refresh_token),
            device_name=device_name or "Unknown",
            device_type=device_type or "web",
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def validate_refresh_token(self, refresh_token: str) -> User | None:
        """Validate refresh token by checking the hashed value in device_sessions."""
        try:
            payload = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])
            if payload.get("type") != "refresh":
                return None
            user_id = payload.get("sub")
            if not user_id:
                return None
        except JWTError:
            return None

        token_hash = _hash_token(refresh_token)
        result = await self.db.execute(
            select(DeviceSession).where(
                DeviceSession.refresh_token_hash == token_hash,
                DeviceSession.is_active == True,
                DeviceSession.expires_at > datetime.now(timezone.utc),
            )
        )
        session = result.scalar_one_or_none()
        if session is None:
            return None

        # Update last used
        session.last_used_at = datetime.now(timezone.utc)
        await self.db.flush()

        return await self.get_user_by_id(uuid.UUID(user_id))

    async def revoke_session(self, session_id: uuid.UUID) -> bool:
        """Revoke a device session (effectively revoking its refresh token)."""
        result = await self.db.execute(
            select(DeviceSession).where(DeviceSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.is_active = False
            await self.db.flush()
            return True
        return False

    async def revoke_all_sessions(self, user_id: uuid.UUID) -> int:
        """Revoke all active sessions for a user."""
        result = await self.db.execute(
            select(DeviceSession).where(
                DeviceSession.user_id == user_id, DeviceSession.is_active == True
            )
        )
        sessions = list(result.scalars().all())
        for s in sessions:
            s.is_active = False
        await self.db.flush()
        return len(sessions)

    async def get_user_from_token(self, token: str) -> User | None:
        """Decode JWT access token and return the corresponding User."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            user_id = payload.get("sub")
            if user_id is None or payload.get("type") != "access":
                return None
        except JWTError:
            return None
        return await self.get_user_by_id(uuid.UUID(user_id))

    # ── Permission Checking ───────────────────────────────────────────────

    async def user_has_permission(self, user: User, permission_code: str) -> bool:
        """Check if user has a specific permission via their roles."""
        for ur in (user.user_roles or []):
            for rp in (ur.role.role_permissions or []):
                if rp.permission.code == permission_code:
                    return True
        return False

    async def get_user_permissions(self, user: User) -> list[str]:
        """Get all permission codes for a user."""
        permissions: list[str] = []
        for ur in (user.user_roles or []):
            for rp in (ur.role.role_permissions or []):
                if rp.permission.code not in permissions:
                    permissions.append(rp.permission.code)
        return permissions

    # ── Password Management ───────────────────────────────────────────────

    async def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        """Change password after verifying current password."""
        if not verify_password(current_password, user.password_hash):
            return False
        user.password_hash = hash_password(new_password)
        await self.db.flush()
        return True

    # ── Role Management ───────────────────────────────────────────────────

    async def get_all_roles(self) -> list[Role]:
        result = await self.db.execute(
            select(Role)
            .options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
            .order_by(Role.name)
        )
        return list(result.scalars().all())

    async def get_all_permissions(self) -> list[Permission]:
        result = await self.db.execute(select(Permission).order_by(Permission.category, Permission.code))
        return list(result.scalars().all())

    async def create_role(self, name: str, display_name: str, description: str | None,
                          permission_ids: list[uuid.UUID]) -> Role:
        role = Role(name=name, display_name=display_name, description=description)
        self.db.add(role)
        await self.db.flush()
        for pid in permission_ids:
            self.db.add(RolePermission(role_id=role.id, permission_id=pid))
        await self.db.flush()
        return role

    async def assign_role(self, user_id: uuid.UUID, role_id: uuid.UUID,
                          assigned_by: uuid.UUID | None = None) -> UserRole:
        ur = UserRole(user_id=user_id, role_id=role_id, assigned_by=assigned_by)
        self.db.add(ur)
        await self.db.flush()
        return ur

    async def remove_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        )
        ur = result.scalar_one_or_none()
        if ur:
            await self.db.delete(ur)
            await self.db.flush()
            return True
        return False
