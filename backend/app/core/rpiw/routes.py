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

router = APIRouter(prefix="/api/v1/rpiw", tags=["RPIW - Role-Based Workspace"])


# ─── Role Management ──────────────────────────────────

@router.post("/roles", response_model=RpiwUserRoleOut)
async def assign_role(data: RpiwUserRoleCreate, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    role = await svc.assign_role(data.model_dump())
    await db.commit()
    return role

@router.get("/roles", response_model=List[RpiwUserRoleOut])
async def get_all_roles(db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    return await svc.get_all_roles()

@router.get("/roles/user/{user_id}", response_model=List[RpiwUserRoleOut])
async def get_user_roles(user_id: str, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    return await svc.get_user_roles(user_id)

@router.get("/roles/user/{user_id}/primary", response_model=RpiwUserRoleOut)
async def get_primary_role(user_id: str, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    role = await svc.get_primary_role(user_id)
    if not role:
        raise HTTPException(status_code=404, detail="No primary role found for user")
    return role


# ─── Workspace Configuration ──────────────────────────────────

@router.get("/workspace/{role_code}")
async def get_workspace_config(role_code: str, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    config = await svc.get_workspace_config(role_code)
    return config


# ─── Permission Management ──────────────────────────────────

@router.get("/permissions/{role_code}", response_model=List[RpiwRolePermissionOut])
async def get_role_permissions(role_code: str, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    return await svc.get_role_permissions(role_code)

@router.get("/permissions/{role_code}/check/{permission_key}")
async def check_permission(role_code: str, permission_key: str, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    has_perm = await svc.check_permission(role_code, permission_key)
    return {"role_code": role_code, "permission_key": permission_key, "allowed": has_perm}


# ─── Workflow Management ──────────────────────────────────

@router.get("/workflows/{role_code}", response_model=List[RpiwRoleWorkflowOut])
async def get_role_workflows(role_code: str, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    return await svc.get_role_workflows(role_code)


# ─── Component Management ──────────────────────────────────

@router.get("/components/{role_code}", response_model=List[RpiwRoleComponentOut])
async def get_role_components(role_code: str, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    return await svc.get_role_components(role_code)


# ─── Session Management ──────────────────────────────────

@router.post("/sessions")
async def create_session(user_id: str, role_code: str, department: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    session = await svc.create_session(user_id, role_code, department)
    await db.commit()
    return session

@router.get("/sessions/{user_id}", response_model=RpiwRoleSessionOut)
async def get_active_session(user_id: str, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    session = await svc.get_active_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="No active session")
    return session


# ─── Activity Logging ──────────────────────────────────

@router.post("/activity-logs", response_model=RpiwActivityLogOut)
async def log_activity(data: RpiwActivityLogCreate, db: AsyncSession = Depends(get_db)):
    svc = RPIWService(db)
    log = await svc.log_activity(data.model_dump())
    await db.commit()
    return log

@router.get("/activity-logs", response_model=List[RpiwActivityLogOut])
async def get_activity_logs(
    user_id: Optional[str] = None,
    role_code: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    svc = RPIWService(db)
    return await svc.get_activity_logs(user_id, role_code, limit)
