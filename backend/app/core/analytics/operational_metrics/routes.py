from fastapi import APIRouter
from app.dependencies import CurrentUser, DBSession
from app.core.analytics.operational_metrics.schemas import OperationalMetricOut
from app.core.analytics.operational_metrics.services import OperationalMetricService

router = APIRouter(prefix="/operational-metrics", tags=["Analytics - Operational"])

@router.get("", response_model=list[OperationalMetricOut])
async def list_operational_metrics(db: DBSession, current_user: CurrentUser):
    svc = OperationalMetricService(db)
    await svc.aggregate_daily()
    return await svc.get_recent_metrics()
