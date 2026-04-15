"""
Auth router – enterprise authentication endpoints.

Endpoints:
- POST /auth/register      — Create user (admin only)
- POST /auth/login          — Authenticate + return tokens
- POST /auth/refresh        — Refresh access token
- POST /auth/logout         — Revoke current session
- GET  /auth/me             — Current user profile
- PUT  /auth/me/password    — Change password
- GET  /auth/sessions       — List device sessions
- DELETE /auth/sessions/{id} — Revoke a session
- GET  /auth/roles          — List all roles
- GET  /auth/permissions    — List all permissions
- POST /auth/roles          — Create role (admin only)
- GET  /auth/users          — List users (admin only)
- POST /auth/users/{id}/roles — Assign role
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.core.auth.schemas import (
    ChangePasswordRequest,
    DeviceSessionOut,
    LoginRequest,
    PermissionOut,
    RefreshRequest,
    RoleCreate,
    RoleOut,
    TokenResponse,
    UserCreate,
    UserListOut,
    UserOut,
    UserUpdate,
)
from app.core.auth.services import AuthService
from app.core.audit.services import AuditService
from app.core.events.models import EventType
from app.core.events.services import EventService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_to_out(user) -> UserOut:
    """Convert User ORM to UserOut schema with roles."""
    roles = []
    for ur in (user.user_roles or []):
        role = ur.role
        perms = [
            PermissionOut(
                id=rp.permission.id,
                code=rp.permission.code,
                display_name=rp.permission.display_name,
                category=rp.permission.category,
                description=rp.permission.description,
            )
            for rp in (role.role_permissions or [])
        ]
        roles.append(RoleOut(
            id=role.id, name=role.name, display_name=role.display_name,
            description=role.description, is_system=role.is_system, permissions=perms,
        ))
    return UserOut(
        id=user.id, email=user.email, first_name=user.first_name,
        last_name=user.last_name, full_name=user.full_name, phone=user.phone,
        status=user.status, last_login_at=user.last_login_at,
        two_factor_enabled=user.two_factor_enabled, created_at=user.created_at,
        roles=roles,
    )


# ── Registration / Login ─────────────────────────────────────────────────

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: DBSession, user: CurrentUser) -> UserOut:
    """Create a new user account (requires manage_users permission). Auto-inherits org_id from the creating admin."""
    try:
        service = AuthService(db)
        new_user = await service.create_user(data, org_id=getattr(user, 'org_id', None))
        await EventService(db).emit(
            EventType.USER_CREATED,
            summary=f"User {new_user.full_name} ({new_user.email}) created",
            actor_id=user.id,
            payload={"user_id": str(new_user.id), "email": new_user.email},
        )
        loaded = await service.get_user_by_id(new_user.id)
        return _user_to_out(loaded)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request, db: DBSession) -> TokenResponse:
    """Authenticate and return JWT tokens with device session tracking."""
    service = AuthService(db)
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    user, error = await service.authenticate(
        data.email, data.password, ip_address=ip,
        device_name=data.device_name, device_type=data.device_type, user_agent=ua,
    )
    if user is None:
        await AuditService(db).log(
            action="login_failed", entity_type="user", entity_id="unknown",
            ip_address=ip, user_agent=ua, new_value={"email": data.email, "error": error},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)

    access_token = service.create_access_token(user)
    refresh_token = service.create_refresh_token(user)

    await service.create_session(
        user, refresh_token, ip_address=ip,
        device_name=data.device_name, device_type=data.device_type, user_agent=ua,
    )

    await AuditService(db).log(
        user_id=user.id, action="user_login", entity_type="user",
        entity_id=str(user.id), ip_address=ip, user_agent=ua,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: DBSession) -> TokenResponse:
    """Issue new access token using refresh token."""
    service = AuthService(db)
    user = await service.validate_refresh_token(body.refresh_token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    return TokenResponse(
        access_token=service.create_access_token(user),
        refresh_token=body.refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(db: DBSession, user: CurrentUser) -> None:
    """Revoke all sessions — effectively logs out everywhere."""
    await AuthService(db).revoke_all_sessions(user.id)
    await AuditService(db).log(
        user_id=user.id, action="user_logout", entity_type="user",
        entity_id=str(user.id),
    )


# ── Current User ──────────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return _user_to_out(user)


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(data: ChangePasswordRequest, db: DBSession, user: CurrentUser) -> None:
    success = await AuthService(db).change_password(user, data.current_password, data.new_password)
    if not success:
        from app.core.i18n import t
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=t("auth.invalid_credentials"))
    await AuditService(db).log(
        user_id=user.id, action="password_changed", entity_type="user", entity_id=str(user.id),
    )


@router.put("/preferences", status_code=status.HTTP_200_OK)
async def update_preferences(data: dict, db: DBSession, user: CurrentUser) -> dict:
    """Update user preferences (like preferred_language)."""
    # Just acknowledging it for now, can be persisted in profile table later
    return {"message": "Preferences updated successfully"}


# ── Forgot Password ──────────────────────────────────────────────────────
import secrets
import time

_reset_tokens: dict[str, dict] = {}  # token -> {"user_id": ..., "expires": ...}


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str



@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: ForgotPasswordRequest, db: DBSession) -> dict:
    """Check if email exists and generate a password reset token."""
    service = AuthService(db)
    user = await service.get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=404, detail="This email is not registered in the system.")

    token = secrets.token_urlsafe(32)
    _reset_tokens[token] = {"user_id": str(user.id), "expires": time.time() + 3600}
    return {
        "message": "Email verified successfully.",
        "reset_token": token,
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: ResetPasswordRequest, db: DBSession) -> dict:
    """Reset password using a valid reset token."""
    token_data = _reset_tokens.get(data.token)
    if not token_data or token_data["expires"] < time.time():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    service = AuthService(db)
    user = await service.get_user_by_id(uuid.UUID(token_data["user_id"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await service.reset_password(user, data.new_password)
    del _reset_tokens[data.token]
    return {"message": "Password has been reset successfully"}

# ── Sessions ──────────────────────────────────────────────────────────────

@router.get("/sessions", response_model=list[DeviceSessionOut])
async def list_sessions(db: DBSession, user: CurrentUser) -> list[DeviceSessionOut]:
    from sqlalchemy import select
    from app.core.auth.models import DeviceSession
    result = await db.execute(
        select(DeviceSession)
        .where(DeviceSession.user_id == user.id, DeviceSession.is_active == True)
        .order_by(DeviceSession.last_used_at.desc())
    )
    return [DeviceSessionOut.model_validate(s) for s in result.scalars().all()]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(session_id: uuid.UUID, db: DBSession, user: CurrentUser) -> None:
    success = await AuthService(db).revoke_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")


# ── Roles & Permissions ──────────────────────────────────────────────────

@router.get("/roles", response_model=list[RoleOut])
async def list_roles(db: DBSession, _: CurrentUser) -> list[RoleOut]:
    roles = await AuthService(db).get_all_roles()
    result = []
    for r in roles:
        perms = [PermissionOut.model_validate(rp.permission) for rp in (r.role_permissions or [])]
        result.append(RoleOut(
            id=r.id, name=r.name, display_name=r.display_name,
            description=r.description, is_system=r.is_system, permissions=perms,
        ))
    return result


@router.get("/permissions", response_model=list[PermissionOut])
async def list_permissions(db: DBSession, _: CurrentUser) -> list[PermissionOut]:
    perms = await AuthService(db).get_all_permissions()
    return [PermissionOut.model_validate(p) for p in perms]


@router.post("/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(data: RoleCreate, db: DBSession, user: CurrentUser) -> RoleOut:
    service = AuthService(db)
    role = await service.create_role(data.name, data.display_name, data.description, data.permission_ids)
    await EventService(db).emit(
        EventType.USER_CREATED,
        summary=f"Role '{role.name}' created",
        actor_id=user.id,
        payload={"role_id": str(role.id)},
    )
    return RoleOut(id=role.id, name=role.name, display_name=role.display_name,
                   description=role.description, is_system=role.is_system, permissions=[])


# ── User Management (admin) ──────────────────────────────────────────────

@router.get("/users", response_model=UserListOut)
async def list_users(
    db: DBSession, user: CurrentUser,
    skip: int = Query(0, ge=0), limit: int = Query(20, le=100),
) -> UserListOut:
    service = AuthService(db)
    users, total = await service.list_users(skip=skip, limit=limit, org_id=getattr(user, 'org_id', None))
    return UserListOut(total=total, items=[_user_to_out(u) for u in users])


@router.post("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_id: uuid.UUID, role_id: uuid.UUID, db: DBSession, user: CurrentUser
) -> dict:
    await AuthService(db).assign_role(user_id, role_id, assigned_by=user.id)
    return {"message": "Role assigned"}


@router.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    user_id: uuid.UUID, role_id: uuid.UUID, db: DBSession, _: CurrentUser
) -> None:
    success = await AuthService(db).remove_role(user_id, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role assignment not found")
