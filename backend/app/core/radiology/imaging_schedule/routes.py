import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from .schemas import ImagingScheduleCreate, ImagingScheduleOut
from .services import ImagingScheduleService

router = APIRouter()

@router.post("/schedule", response_model=ImagingScheduleOut)
async def schedule_radiology_scan(data: ImagingScheduleCreate, db: DBSession, user: CurrentUser):
    return await ImagingScheduleService(db).schedule_scan(data, user.id)
