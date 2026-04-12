import uuid
from fastapi import APIRouter, HTTPException, status
from .schemas import AnesthesiaRecordCreate, AnesthesiaRecordUpdate, AnesthesiaRecordOut
from .services import AnesthesiaRecordService
from app.dependencies import CurrentUser, DBSession


router = APIRouter(prefix="/anesthesia", tags=["Anesthesia Records"])

@router.post("/", response_model=AnesthesiaRecordOut, status_code=status.HTTP_201_CREATED)
async def create_record(data: AnesthesiaRecordCreate, db: DBSession, _: CurrentUser) -> AnesthesiaRecordOut:
    return await AnesthesiaRecordService.create_record(db, data)

@router.get("/{schedule_id}", response_model=AnesthesiaRecordOut)
async def get_record(schedule_id: uuid.UUID, db: DBSession, _: CurrentUser) -> AnesthesiaRecordOut:
    record = await AnesthesiaRecordService.get_record(db, schedule_id)
    if not record:
        raise HTTPException(status_code=404, detail="Anesthesia record not found for this schedule")
    return record

@router.put("/{schedule_id}", response_model=AnesthesiaRecordOut)
async def update_record(schedule_id: uuid.UUID, data: AnesthesiaRecordUpdate, db: DBSession, _: CurrentUser) -> AnesthesiaRecordOut:
    record = await AnesthesiaRecordService.update_record(db, schedule_id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Anesthesia record not found for this schedule")
    return record
