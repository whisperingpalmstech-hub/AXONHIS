import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from .schemas import MedicationCreate, MedicationOut
from .services import MedicationService

router = APIRouter(tags=["pharmacy-medications"])

@router.post("/medications", response_model=MedicationOut)
async def create_medication(data: MedicationCreate, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    return await svc.create_medication(data)

@router.get("/medications/{med_id}", response_model=MedicationOut)
async def get_medication(med_id: uuid.UUID, db: DBSession, _: CurrentUser):
    svc = MedicationService(db)
    return await svc.get_medication(med_id)

@router.get("/medications", response_model=list[MedicationOut])
async def list_medications(db: DBSession, _: CurrentUser, limit: int = 100):
    svc = MedicationService(db)
    return await svc.list_medications(limit=limit)
