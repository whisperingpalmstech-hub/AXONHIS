import uuid
from fastapi import APIRouter, status
from .schemas import SurgeryEventCreate, SurgeryEventOut
from .services import SurgeryEventService
from app.dependencies import CurrentUser, DBSession


router = APIRouter(prefix="/event", tags=["Surgery Events"])

@router.post("/", response_model=SurgeryEventOut, status_code=status.HTTP_201_CREATED)
async def record_event(data: SurgeryEventCreate, db: DBSession, user: CurrentUser) -> SurgeryEventOut:
    if not data.recorded_by:
        data.recorded_by = user.id
    return await SurgeryEventService.record_event(db, data)

@router.get("/{schedule_id}", response_model=list[SurgeryEventOut])
async def list_events_for_schedule(schedule_id: uuid.UUID, db: DBSession, _: CurrentUser) -> list[SurgeryEventOut]:
    return await SurgeryEventService.get_events_for_schedule(db, schedule_id)
