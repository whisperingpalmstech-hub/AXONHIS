from fastapi import APIRouter, status
import uuid
from app.core.patients.guardians.schemas import PatientGuardianCreate, PatientGuardianOut
from app.core.patients.guardians.services import GuardianService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/patients/{patient_id}/guardians", tags=["patient-guardians"])

@router.post("/", response_model=PatientGuardianOut, status_code=status.HTTP_201_CREATED)
async def add_guardian(patient_id: uuid.UUID, data: PatientGuardianCreate, db: DBSession, _: CurrentUser):
    return await GuardianService(db).add_guardian(patient_id, data)

@router.get("/", response_model=list[PatientGuardianOut])
async def list_guardians(patient_id: uuid.UUID, db: DBSession, _: CurrentUser):
    return await GuardianService(db).list_guardians(patient_id)
