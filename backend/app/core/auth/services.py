"""
Auth services – user creation, authentication, JWT handling.

No HTTP concerns live here; all business logic is pure service methods.
"""
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth.models import User, UserRole
from app.core.auth.schemas import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_jwt(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user with a hashed password."""
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=_hash_password(data.password),
            role=UserRole(data.role),
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        """Return the user if credentials are valid, else None."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None or not _verify_password(password, user.hashed_password):
            return None
        return user

    def create_access_token(self, user: User) -> str:
        return _create_jwt(
            {"sub": str(user.id), "role": user.role, "type": "access"},
            timedelta(minutes=settings.access_token_expire_minutes),
        )

    def create_refresh_token(self, user: User) -> str:
        return _create_jwt(
            {"sub": str(user.id), "type": "refresh"},
            timedelta(days=settings.refresh_token_expire_days),
        )

    async def get_user_from_token(self, token: str) -> User | None:
        """Decode JWT and return the corresponding User."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            user_id: str | None = payload.get("sub")
            if user_id is None or payload.get("type") != "access":
                return None
        except JWTError:
            return None
        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        return result.scalar_one_or_none()
