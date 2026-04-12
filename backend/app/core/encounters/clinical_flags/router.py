import uuid
from fastapi import APIRouter, status
from app.core.encounters.clinical_flags.schemas import ClinicalFlagCreate, ClinicalFlagOut
from app.core.encounters.clinical_flags.services import ClinicalFlagService
from app.dependencies import CurrentUser, DBSession

# Note: Flags are tied to the PATIENT, not just a single encounter.
router = APIRouter(prefix="/patients/{patient_id}/flags", tags=["clinical-flags"])

@router.post("/", response_model=ClinicalFlagOut, status_code=status.HTTP_201_CREATED)
async def add_flag(patient_id: uuid.UUID, data: ClinicalFlagCreate, db: DBSession, _: CurrentUser):
    return await ClinicalFlagService(db).add_flag(patient_id, data)

@router.get("/", response_model=list[ClinicalFlagOut])
async def get_flags(patient_id: uuid.UUID, db: DBSession, _: CurrentUser):
    return await ClinicalFlagService(db).get_patient_flags(patient_id)
