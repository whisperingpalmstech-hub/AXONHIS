from fastapi import APIRouter
from app.dependencies import CurrentUser, DBSession
from app.core.analytics.clinical_metrics.schemas import ClinicalMetricOut
from app.core.analytics.clinical_metrics.services import ClinicalMetricService

router = APIRouter(prefix="/clinical-metrics", tags=["Analytics - Clinical"])

@router.get("", response_model=list[ClinicalMetricOut])
async def list_clinical_metrics(db: DBSession, current_user: CurrentUser):
    svc = ClinicalMetricService(db)
    # Ensure something exists
    await svc.aggregate_daily()
    return await svc.get_recent_metrics()
