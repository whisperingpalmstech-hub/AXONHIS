"""
Shared FastAPI dependencies.

Provides:
- DBSession: async database session
- CurrentUser: authenticated user from JWT
- require_permissions: decorator for permission-based access control
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import User
from app.core.auth.services import AuthService
from app.database import get_db

bearer_scheme = HTTPBearer(auto_error=False)

DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DBSession,
) -> User:
    """Validate JWT bearer token and return the authenticated user with roles loaded."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    user = await AuthService(db).get_user_from_token(token)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permissions(*permission_codes: str):
    """
    Dependency factory: restrict endpoint to users with specific permissions.

    Usage:
        @router.get("/admin", dependencies=[require_permissions("system_admin")])
        async def admin_endpoint(): ...
    """

    async def _check(current_user: CurrentUser) -> User:
        user_perms: list[str] = []
        for ur in (current_user.user_roles or []):
            for rp in (ur.role.role_permissions or []):
                if rp.permission.code not in user_perms:
                    user_perms.append(rp.permission.code)

        # system_admin bypass — has all permissions
        if "system_admin" in user_perms:
            return current_user

        for required in permission_codes:
            if required not in user_perms:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{required}' is required for this action",
                )
        return current_user

    return Depends(_check)
