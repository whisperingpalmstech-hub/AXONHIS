from fastapi import APIRouter
from app.dependencies import CurrentUser, DBSession
from app.core.analytics.predictive_models.schemas import HospitalPredictionOut
from app.core.analytics.predictive_models.services import PredictiveModelService
from typing import Optional

router = APIRouter(prefix="/predictions", tags=["Analytics - Predictive"])

@router.get("", response_model=list[HospitalPredictionOut])
async def list_predictions(
    db: DBSession, 
    current_user: CurrentUser,
    prediction_type: Optional[str] = None
):
    svc = PredictiveModelService(db)
    await svc.generate_forecasts()
    return await svc.get_predictions(prediction_type)
