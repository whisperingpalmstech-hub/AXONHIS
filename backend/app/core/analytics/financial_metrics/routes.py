from fastapi import APIRouter
from app.dependencies import CurrentUser, DBSession
from app.core.analytics.financial_metrics.schemas import FinancialMetricOut
from app.core.analytics.financial_metrics.services import FinancialMetricService

router = APIRouter(prefix="/financial-metrics", tags=["Analytics - Financial"])

@router.get("", response_model=list[FinancialMetricOut])
async def list_financial_metrics(db: DBSession, current_user: CurrentUser):
    svc = FinancialMetricService(db)
    await svc.aggregate_daily()
    return await svc.get_recent_metrics()
