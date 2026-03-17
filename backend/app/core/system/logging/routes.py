from fastapi import APIRouter, Depends
from app.dependencies import DBSession, CurrentUser, require_permissions
from .schemas import LogOut
from .services import CentralLogger

router = APIRouter(prefix="/system/logs", tags=["system-logging"], dependencies=[require_permissions("system_admin")])

@router.get("", response_model=list[LogOut])
async def list_logs(db: DBSession, _: CurrentUser, skip: int = 0, limit: int = 100):
    logger_service = CentralLogger(db)
    return await logger_service.get_logs(limit, skip)
