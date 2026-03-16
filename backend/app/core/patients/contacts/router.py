from fastapi import APIRouter, status
import uuid
from app.core.patients.contacts.schemas import PatientContactCreate, PatientContactOut
from app.core.patients.contacts.services import ContactService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/patients/{patient_id}/contacts", tags=["patient-contacts"])

@router.post("/", response_model=PatientContactOut, status_code=status.HTTP_201_CREATED)
async def add_contact(patient_id: uuid.UUID, data: PatientContactCreate, db: DBSession, _: CurrentUser):
    return await ContactService(db).add_contact(patient_id, data)

@router.get("/", response_model=list[PatientContactOut])
async def list_contacts(patient_id: uuid.UUID, db: DBSession, _: CurrentUser):
    return await ContactService(db).list_contacts(patient_id)
