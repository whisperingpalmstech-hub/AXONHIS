from typing import Annotated
import uuid

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.core.patients.patients.schemas import PatientCreate, PatientUpdate, PatientOut
from app.core.patients.patients.services import PatientService
from app.dependencies import CurrentUser, DBSession


class DuplicateCheckRequest(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    phone: str | None = None

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def create_patient(data: PatientCreate, db: DBSession, user: CurrentUser) -> PatientOut:
    """Create a new patient."""
    service = PatientService(db, user)
    try:
        new_patient = await service.create_patient(data)
        return new_patient
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient identity conflict.")

@router.get("/", response_model=list[PatientOut])
async def list_patients(db: DBSession, user: CurrentUser, skip: int = 0, limit: int = 20) -> list[PatientOut]:
    service = PatientService(db, user)
    patients = await service.list_patients(skip=skip, limit=limit)
    return patients

@router.get("/search", response_model=list[PatientOut])
async def search_patients(query: str, db: DBSession, user: CurrentUser, limit: int = 20) -> list[PatientOut]:
    """Enterprise Patient Search Engine using fuzzy matching on name, phone, identifier."""
    service = PatientService(db, user)
    patients = await service.search_patients(query=query, limit=limit)
    return patients

@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(patient_id: uuid.UUID, db: DBSession, user: CurrentUser) -> PatientOut:
    service = PatientService(db, user)
    patient = await service.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.put("/{patient_id}", response_model=PatientOut)
async def update_patient(patient_id: uuid.UUID, data: PatientUpdate, db: DBSession, user: CurrentUser) -> PatientOut:
    service = PatientService(db, user)
    patient = await service.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return await service.update_patient(patient, data)

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: uuid.UUID, db: DBSession, user: CurrentUser):
    service = PatientService(db, user)
    patient = await service.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    await db.delete(patient)
    await db.flush()

@router.post("/detect-duplicates", status_code=status.HTTP_200_OK)
async def detect_duplicates(data: DuplicateCheckRequest, db: DBSession, user: CurrentUser):
    """Check for duplicate records during registration workflow. Accepts JSON body."""
    service = PatientService(db, user)
    duplicates = await service.detect_duplicates(
        data.first_name, data.last_name, data.date_of_birth, data.phone
    )

    res = []
    for dup in duplicates:
        res.append({
            "patient": {
                "id": str(dup.patient.id),
                "patient_uuid": dup.patient.patient_uuid,
                "first_name": dup.patient.first_name,
                "last_name": dup.patient.last_name,
                "date_of_birth": str(dup.patient.date_of_birth),
                "primary_phone": dup.patient.primary_phone,
            },
            "confidence_score": dup.confidence_score
        })
    return res

@router.post("/merge", status_code=status.HTTP_200_OK)
async def merge_patients(source_id: uuid.UUID, target_id: uuid.UUID, db: DBSession, user: CurrentUser):
    # This is a complex endpoint to merge records. We flag the source as "merged".
    service = PatientService(db, user)
    source = await service.get_patient_by_id(source_id)
    target = await service.get_patient_by_id(target_id)
    if not source or not target:
        raise HTTPException(status_code=404, detail="One or both patients not found")
    
    # Normally we would reassign all related identifying records to the target.
    # For Phase 2 simplicity:
    source.status = "merged"
    await db.flush()
    return {"message": "Patients merged successfully", "merged_into": str(target.id)}
