import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from .schemas import PrescriptionCreate, PrescriptionOut
from .services import PrescriptionService

router = APIRouter(tags=["pharmacy-prescriptions"])

@router.post("/prescriptions", response_model=PrescriptionOut)
async def create_prescription(data: PrescriptionCreate, db: DBSession, _: CurrentUser):
    svc = PrescriptionService(db)
    return await svc.create_prescription(data)

@router.get("/prescriptions/{rx_id}", response_model=PrescriptionOut)
async def get_prescription(rx_id: uuid.UUID, db: DBSession, _: CurrentUser):
    svc = PrescriptionService(db)
    return await svc.get_prescription(rx_id)

@router.get("/prescriptions", response_model=list[PrescriptionOut])
async def list_prescriptions(db: DBSession, _: CurrentUser, limit: int = 100):
    svc = PrescriptionService(db)
    return await svc.list_prescriptions(limit=limit)
