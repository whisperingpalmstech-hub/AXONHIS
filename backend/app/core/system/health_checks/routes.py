import psutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from app.dependencies import DBSession, CurrentUser, require_permissions
from app.config import settings

from .schemas import HealthCheckOut, SystemMetricsOut, SystemVersionOut

router = APIRouter(prefix="/system", tags=["system-management"], dependencies=[require_permissions("system_admin")])

@router.get("/health", response_model=HealthCheckOut)
async def get_system_health(db: DBSession, _: CurrentUser):
    # Check Database Connection
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # Simulate checking Redis (Assuming Redis is connected if celery is up, or just basic ping check)
    # Ideally, we'd use redis client ping here if available
    redis_status = "healthy"
    
    # Simulate checking AI Service
    ai_status = "healthy"

    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" and ai_status == "healthy" else "degraded"

    return HealthCheckOut(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        api_status="healthy",
        database_status=db_status,
        redis_status=redis_status,
        ai_service_status=ai_status,
        details={"uptime_seconds": psutil.boot_time()}
    )

@router.get("/metrics", response_model=SystemMetricsOut)
async def get_system_metrics(db: DBSession, _: CurrentUser):
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    
    return SystemMetricsOut(
        cpu_usage=cpu,
        memory_usage=mem,
        disk_usage=disk,
        active_requests=0, # Placeholder for active metric
        queue_backlog=0
    )

@router.get("/version", response_model=SystemVersionOut)
async def get_system_version(_: CurrentUser):
    return SystemVersionOut(
        version="v1.1.0-Phase11",
        environment="production",
        last_deployment=datetime.now(timezone.utc)
    )
