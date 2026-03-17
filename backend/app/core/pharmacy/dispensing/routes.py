import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from .schemas import DispensingRecordCreate, DispensingRecordOut
from .services import DispensingService

router = APIRouter(tags=["pharmacy-dispensing"])

@router.post("/dispense", response_model=DispensingRecordOut)
async def dispense_prescription(data: DispensingRecordCreate, db: DBSession, user: CurrentUser):
    svc = DispensingService(db)
    return await svc.dispense_prescription(data, user.id)

@router.get("/dispense", response_model=list[DispensingRecordOut])
async def list_dispensing_records(db: DBSession, _: CurrentUser, limit: int = 100):
    svc = DispensingService(db)
    return await svc.list_dispensing_records(limit=limit)
