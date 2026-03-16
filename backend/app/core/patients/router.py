"""Patients router – CRUD and search endpoints."""
import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.core.events.models import EventType
from app.core.events.services import EventService
from app.core.patients.schemas import PatientCreate, PatientListOut, PatientOut, PatientUpdate
from app.core.patients.services import PatientService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def create_patient(data: PatientCreate, db: DBSession, user: CurrentUser) -> PatientOut:
    service = PatientService(db)
    patient = await service.create(data)
    await EventService(db).emit(
        event_type=EventType.PATIENT_REGISTERED,
        summary=f"Patient {patient.full_name} registered (MRN: {patient.mrn})",
        patient_id=patient.id,
        actor_id=user.id,
        payload={"mrn": patient.mrn},
    )
    return PatientOut.model_validate(patient)


@router.get("", response_model=PatientListOut)
async def list_patients(
    db: DBSession,
    _: CurrentUser,
    q: str | None = Query(default=None, description="Search name/MRN/phone"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100),
) -> PatientListOut:
    service = PatientService(db)
    if q:
        patients, total = await service.search(q, skip=skip, limit=limit)
    else:
        patients, total = await service.list_all(skip=skip, limit=limit)
    return PatientListOut(total=total, items=[PatientOut.model_validate(p) for p in patients])


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(patient_id: uuid.UUID, db: DBSession, _: CurrentUser) -> PatientOut:
    patient = await PatientService(db).get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return PatientOut.model_validate(patient)


@router.put("/{patient_id}", response_model=PatientOut)
async def update_patient(
    patient_id: uuid.UUID, data: PatientUpdate, db: DBSession, user: CurrentUser
) -> PatientOut:
    service = PatientService(db)
    patient = await service.get_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    await EventService(db).emit(
        EventType.PATIENT_UPDATED,
        summary=f"Patient record updated for {patient.full_name}",
        patient_id=patient.id,
        actor_id=user.id,
    )
    patient = await service.update(patient, data)
    return PatientOut.model_validate(patient)
