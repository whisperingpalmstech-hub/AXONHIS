from fastapi import APIRouter, Depends
from app.dependencies import DBSession, CurrentUser, require_permissions
from .schemas import TrackedErrorOut, PerformanceMetricOut
from .services import MonitoringService

router = APIRouter(prefix="/system/monitoring", tags=["system-monitoring"], dependencies=[require_permissions("system_admin")])

@router.get("/errors", response_model=list[TrackedErrorOut])
async def list_errors(db: DBSession, _: CurrentUser, skip: int = 0, limit: int = 100):
    service = MonitoringService(db)
    return await service.get_errors(limit, skip)

@router.get("/performance", response_model=list[PerformanceMetricOut])
async def list_performance_metrics(db: DBSession, _: CurrentUser, skip: int = 0, limit: int = 100):
    service = MonitoringService(db)
    return await service.get_performance_metrics(limit, skip)
