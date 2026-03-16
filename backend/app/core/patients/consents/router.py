from fastapi import APIRouter, status
import uuid
from app.core.patients.consents.schemas import PatientConsentCreate, PatientConsentOut
from app.core.patients.consents.services import ConsentService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/patients/{patient_id}/consents", tags=["patient-consents"])

@router.post("/", response_model=PatientConsentOut, status_code=status.HTTP_201_CREATED)
async def add_consent(patient_id: uuid.UUID, data: PatientConsentCreate, db: DBSession, _: CurrentUser):
    return await ConsentService(db).add_consent(patient_id, data)

@router.get("/", response_model=list[PatientConsentOut])
async def list_consents(patient_id: uuid.UUID, db: DBSession, _: CurrentUser):
    return await ConsentService(db).list_consents(patient_id)
