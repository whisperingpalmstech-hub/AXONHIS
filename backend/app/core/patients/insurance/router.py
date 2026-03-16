from fastapi import APIRouter, status
import uuid
from app.core.patients.insurance.schemas import PatientInsuranceCreate, PatientInsuranceOut
from app.core.patients.insurance.services import InsuranceService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/patients/{patient_id}/insurance", tags=["patient-insurance"])

@router.post("/", response_model=PatientInsuranceOut, status_code=status.HTTP_201_CREATED)
async def add_insurance(patient_id: uuid.UUID, data: PatientInsuranceCreate, db: DBSession, _: CurrentUser):
    return await InsuranceService(db).add_insurance(patient_id, data)

@router.get("/", response_model=list[PatientInsuranceOut])
async def list_insurance(patient_id: uuid.UUID, db: DBSession, _: CurrentUser):
    return await InsuranceService(db).list_insurance(patient_id)
