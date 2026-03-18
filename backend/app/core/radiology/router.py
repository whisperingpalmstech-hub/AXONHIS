from fastapi import APIRouter
from app.core.radiology.imaging_orders.routes import router as orders_router
from app.core.radiology.imaging_schedule.routes import router as schedule_router
from app.core.radiology.imaging_studies.routes import router as studies_router
from app.core.radiology.radiology_reports.routes import router as reports_router

router = APIRouter(prefix="/radiology", tags=["Radiology & Imaging"])

# Include sub-routers
router.include_router(orders_router)
router.include_router(schedule_router)
router.include_router(studies_router)
router.include_router(reports_router)
