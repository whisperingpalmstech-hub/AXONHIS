from fastapi import APIRouter
from app.dependencies import CurrentUser, DBSession

# Importing services
from app.core.analytics.clinical_metrics.services import ClinicalMetricService
from app.core.analytics.financial_metrics.services import FinancialMetricService
from app.core.analytics.operational_metrics.services import OperationalMetricService
from app.core.analytics.predictive_models.services import PredictiveModelService

from app.core.analytics.predictive_models.schemas import HospitalPredictionOut

router = APIRouter(prefix="/dashboards", tags=["Analytics - Dashboards"])

@router.get("/executive")
async def get_executive_dashboard(db: DBSession, current_user: CurrentUser):
    """Aggregated JSON payload for the main hospital executive dashboard."""
    # Note: Using days=1 for instantaneous metrics
    cs = ClinicalMetricService(db)
    fs = FinancialMetricService(db)
    os = OperationalMetricService(db)
    ps = PredictiveModelService(db)

    c_metric = await cs.aggregate_daily()
    f_metric = await fs.aggregate_daily()
    o_metric = await os.aggregate_daily()
    
    await ps.generate_forecasts()
    predictions = await ps.get_predictions()

    return {
        "daily_admissions": c_metric.admissions_count,
        "average_los_hours": c_metric.average_los_hours,
        "critical_alerts_count": c_metric.critical_alerts_count,

        "daily_revenue": f_metric.daily_revenue,
        "outstanding_invoices_amount": f_metric.outstanding_invoices_amount,
        
        "bed_occupancy_rate": o_metric.bed_occupancy_rate,
        "pending_tasks": o_metric.patient_throughput, # Mapping arbitrarily for example

        "predictions": [HospitalPredictionOut.model_validate(p).model_dump(mode='json') for p in predictions[:5]] # Latest 5 forecasts
    }
