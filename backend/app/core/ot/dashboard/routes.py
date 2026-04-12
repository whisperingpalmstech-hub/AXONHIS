from fastapi import APIRouter
from .services import OTDashboardService
from app.dependencies import CurrentUser, DBSession


router = APIRouter(prefix="/dashboard", tags=["OT Dashboard"])

@router.get("/")
async def get_dashboard(db: DBSession, _: CurrentUser):
    return await OTDashboardService.get_dashboard_summary(db)
