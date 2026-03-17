from fastapi import APIRouter
from app.core.analytics.dashboards.routes import router as dashboards_router
from app.core.analytics.clinical_metrics.routes import router as clinical_router
from app.core.analytics.financial_metrics.routes import router as financial_router
from app.core.analytics.operational_metrics.routes import router as operational_router
from app.core.analytics.predictive_models.routes import router as predictive_router
from app.core.analytics.reports.routes import router as reports_router

router = APIRouter(prefix="/analytics")
router.include_router(dashboards_router)
router.include_router(clinical_router)
router.include_router(financial_router)
router.include_router(operational_router)
router.include_router(predictive_router)
router.include_router(reports_router)
