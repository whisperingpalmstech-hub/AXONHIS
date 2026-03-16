from typing import Annotated
import uuid

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from sqlalchemy.exc import IntegrityError

from app.core.patients.patients.schemas import PatientCreate, PatientUpdate, PatientOut
from app.core.patients.patients.services import PatientService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def create_patient(data: PatientCreate, db: DBSession, user: CurrentUser) -> PatientOut:
    """Create a new patient."""
    service = PatientService(db)
    try:
        new_patient = await service.create_patient(data)
        return new_patient
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient identity conflict.")

@router.get("/", response_model=list[PatientOut])
async def list_patients(db: DBSession, _: CurrentUser, skip: int = 0, limit: int = 20) -> list[PatientOut]:
    service = PatientService(db)
    patients = await service.list_patients(skip=skip, limit=limit)
    return patients

@router.get("/search", response_model=list[PatientOut])
async def search_patients(query: str, db: DBSession, _: CurrentUser, limit: int = 20) -> list[PatientOut]:
    """Enterprise Patient Search Engine using fuzzy matching on name, phone, identifier."""
    service = PatientService(db)
    patients = await service.search_patients(query=query, limit=limit)
    return patients

@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(patient_id: uuid.UUID, db: DBSession, _: CurrentUser) -> PatientOut:
    service = PatientService(db)
    patient = await service.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.put("/{patient_id}", response_model=PatientOut)
async def update_patient(patient_id: uuid.UUID, data: PatientUpdate, db: DBSession, _: CurrentUser) -> PatientOut:
    service = PatientService(db)
    patient = await service.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return await service.update_patient(patient, data)

@router.post("/detect-duplicates", status_code=status.HTTP_200_OK)
async def detect_duplicates(
    first_name: str, last_name: str, date_of_birth: str, db: DBSession, _: CurrentUser, phone: str = Query(None)
):
    """Check for duplicate records during registration workflow."""
    service = PatientService(db)
    duplicates = await service.detect_duplicates(first_name, last_name, date_of_birth, phone)
    
    # We map back into PatientOut with a score
    res = []
    for dup in duplicates:
        # Re-fetch or rely on model dump (since the patient doesn't have loaded relationships here easily)
        # For simplicity, we just return the basic info in duplicate result.
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
async def merge_patients(source_id: uuid.UUID, target_id: uuid.UUID, db: DBSession, _: CurrentUser):
    # This is a complex endpoint to merge records. We flag the source as "merged".
    service = PatientService(db)
    source = await service.get_patient_by_id(source_id)
    target = await service.get_patient_by_id(target_id)
    if not source or not target:
        raise HTTPException(status_code=404, detail="One or both patients not found")
    
    # Normally we would reassign all related identifying records to the target.
    # For Phase 2 simplicity:
    source.status = "merged"
    await db.flush()
    return {"message": "Patients merged successfully", "merged_into": str(target.id)}
