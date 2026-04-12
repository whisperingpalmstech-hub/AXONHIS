from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from .schemas import (
    RpiwUserRoleCreate, RpiwUserRoleOut,
    RpiwRolePermissionOut,
    RpiwRoleWorkflowOut,
    RpiwRoleComponentOut,
    RpiwRoleSessionOut,
    RpiwActivityLogCreate, RpiwActivityLogOut,
    RpiwWorkspaceConfig,
)
from .services import RPIWService
from app.dependencies import CurrentUser

router = APIRouter(prefix="/api/v1/rpiw", tags=["RPIW - Role-Based Workspace"])


# ─── Role Management ──────────────────────────────────

@router.post("/roles", response_model=RpiwUserRoleOut)
async def assign_role(data: RpiwUserRoleCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    role = await svc.assign_role(data.model_dump(), org_id=user.org_id)
    await db.commit()
    return role

@router.get("/roles", response_model=List[RpiwUserRoleOut])
async def get_all_roles(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    return await svc.get_all_roles(org_id=user.org_id)

@router.get("/roles/user/{user_id}", response_model=List[RpiwUserRoleOut])
async def get_user_roles(user_id: str, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    return await svc.get_user_roles(user_id, org_id=user.org_id)

@router.get("/roles/user/{user_id}/primary", response_model=RpiwUserRoleOut)
async def get_primary_role(user_id: str, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    role = await svc.get_primary_role(user_id, org_id=user.org_id)
    if not role:
        raise HTTPException(status_code=404, detail="No primary role found for user in your organization")
    return role


# ─── Workspace Configuration ──────────────────────────────────

@router.get("/workspace/{role_code}")
async def get_workspace_config(role_code: str, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    config = await svc.get_workspace_config(role_code, org_id=user.org_id)
    return config


# ─── Permission Management ──────────────────────────────────

@router.get("/permissions/{role_code}", response_model=List[RpiwRolePermissionOut])
async def get_role_permissions(role_code: str, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    return await svc.get_role_permissions(role_code, org_id=user.org_id)

@router.get("/permissions/{role_code}/check/{permission_key}")
async def check_permission(role_code: str, permission_key: str, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    has_perm = await svc.check_permission(role_code, permission_key, org_id=user.org_id)
    return {"role_code": role_code, "permission_key": permission_key, "allowed": has_perm}


# ─── Workflow Management ──────────────────────────────────

@router.get("/workflows/{role_code}", response_model=List[RpiwRoleWorkflowOut])
async def get_role_workflows(role_code: str, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    return await svc.get_role_workflows(role_code, org_id=user.org_id)


# ─── Component Management ──────────────────────────────────

@router.get("/components/{role_code}", response_model=List[RpiwRoleComponentOut])
async def get_role_components(role_code: str, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    return await svc.get_role_components(role_code, org_id=user.org_id)


# ─── Session Management ──────────────────────────────────

@router.post("/sessions")
async def create_session(user_id: str, role_code: str, user: CurrentUser, department: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    session = await svc.create_session(user_id, role_code, department, org_id=user.org_id)
    await db.commit()
    return session

@router.get("/sessions/{user_id}", response_model=RpiwRoleSessionOut)
async def get_active_session(user_id: str, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    session = await svc.get_active_session(user_id, org_id=user.org_id)
    if not session:
        raise HTTPException(status_code=404, detail="No active session found for your organization")
    return session


# ─── Activity Logging ──────────────────────────────────

@router.post("/activity-logs", response_model=RpiwActivityLogOut)
async def log_activity(data: RpiwActivityLogCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    log = await svc.log_activity(data.model_dump(), org_id=user.org_id)
    await db.commit()
    return log

@router.get("/activity-logs", response_model=List[RpiwActivityLogOut])
async def get_activity_logs(
    user: CurrentUser,
    user_id: Optional[str] = None,
    role_code: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    svc = RPIWService(db)
    return await svc.get_activity_logs(user_id, role_code, limit, org_id=user.org_id)
