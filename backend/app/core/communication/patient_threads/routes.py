import uuid
from fastapi import APIRouter, status
from app.dependencies import DBSession, CurrentUser
from .schemas import PatientThreadOut
from .services import PatientThreadService

router = APIRouter(prefix="/patient_thread", tags=["Communication - Patient Threads"])

@router.post("/{patient_id}", response_model=PatientThreadOut, status_code=status.HTTP_201_CREATED)
async def get_or_create_patient_thread(patient_id: uuid.UUID, db: DBSession, user: CurrentUser) -> PatientThreadOut:
    return await PatientThreadService.get_or_create_thread(db, patient_id, created_by=user.id)
