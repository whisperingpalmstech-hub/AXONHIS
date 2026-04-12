from fastapi import APIRouter, status
import uuid
from app.core.patients.identifiers.schemas import PatientIdentifierCreate, PatientIdentifierOut
from app.core.patients.identifiers.services import IdentifierService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/patients/{patient_id}/identifiers", tags=["patient-identifiers"])

@router.post("/", response_model=PatientIdentifierOut, status_code=status.HTTP_201_CREATED)
async def add_identifier(patient_id: uuid.UUID, data: PatientIdentifierCreate, db: DBSession, _: CurrentUser):
    return await IdentifierService(db).add_identifier(patient_id, data)

@router.get("/", response_model=list[PatientIdentifierOut])
async def list_identifiers(patient_id: uuid.UUID, db: DBSession, _: CurrentUser):
    return await IdentifierService(db).list_identifiers(patient_id)
