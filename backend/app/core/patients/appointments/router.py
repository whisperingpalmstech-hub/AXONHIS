from typing import Annotated
import uuid

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from app.core.patients.appointments.schemas import AppointmentCreate, AppointmentUpdate, AppointmentOut
from app.core.patients.appointments.services import AppointmentService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.post("/", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def schedule_appointment(patient_id: uuid.UUID, data: AppointmentCreate, db: DBSession, user: CurrentUser) -> AppointmentOut:
    service = AppointmentService(db)
    return await service.schedule_appointment(patient_id, data)

@router.get("/{patient_id}", response_model=list[AppointmentOut])
async def list_appointments(patient_id: uuid.UUID, db: DBSession, _: CurrentUser) -> list[AppointmentOut]:
    service = AppointmentService(db)
    return await service.list_patient_appointments(patient_id)

@router.put("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(appointment_id: uuid.UUID, data: AppointmentUpdate, db: DBSession, _: CurrentUser) -> AppointmentOut:
    service = AppointmentService(db)
    appointment = await service.get_appointment(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return await service.update_appointment(appointment, data)
