import uuid
from fastapi import APIRouter, HTTPException, status
from .schemas import SurgeryScheduleCreate, SurgeryScheduleUpdate, SurgeryScheduleOut
from .services import SurgeryScheduleService
from app.dependencies import CurrentUser, DBSession


router = APIRouter(prefix="/schedule", tags=["Surgery Schedule"])

@router.post("/", response_model=SurgeryScheduleOut, status_code=status.HTTP_201_CREATED)
async def schedule_surgery(data: SurgeryScheduleCreate, db: DBSession, user: CurrentUser) -> SurgeryScheduleOut:
    if not data.scheduled_by:
        data.scheduled_by = user.id
    return await SurgeryScheduleService.schedule_surgery(db, data)

@router.get("/", response_model=list[SurgeryScheduleOut])
async def list_schedules(db: DBSession, _: CurrentUser) -> list[SurgeryScheduleOut]:
    return await SurgeryScheduleService.get_all_schedules(db)

@router.get("/{schedule_id}", response_model=SurgeryScheduleOut)
async def get_schedule(schedule_id: uuid.UUID, db: DBSession, _: CurrentUser) -> SurgeryScheduleOut:
    schedule = await SurgeryScheduleService.get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Surgery schedule not found")
    return schedule

@router.put("/{schedule_id}", response_model=SurgeryScheduleOut)
async def update_schedule(schedule_id: uuid.UUID, data: SurgeryScheduleUpdate, db: DBSession, _: CurrentUser) -> SurgeryScheduleOut:
    schedule = await SurgeryScheduleService.update_schedule(db, schedule_id, data)
    if not schedule:
        raise HTTPException(status_code=404, detail="Surgery schedule not found")
    return schedule

@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_surgery(schedule_id: uuid.UUID, db: DBSession, _: CurrentUser):
    if not await SurgeryScheduleService.cancel_surgery(db, schedule_id):
        raise HTTPException(status_code=404, detail="Surgery schedule not found")
