from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import DBSession
from .services import AppointmentPortalService
from .models import AppointmentType
import uuid
from datetime import date, datetime

router = APIRouter(prefix="/appointments", tags=["Patient Portal - Appointments"])

@router.get("/doctors")
async def get_doctors(db: DBSession, patient_id: str, department: str | None = None):
    return await AppointmentPortalService.get_available_doctors(db, uuid.UUID(patient_id), department)

@router.get("/my")
async def get_my_appointments(db: DBSession, patient_id: str):
    return await AppointmentPortalService.get_patient_appointments(db, uuid.UUID(patient_id))

@router.get("/slots")
async def get_doctor_slots(db: DBSession, doctor_id: str, date: date):
    return await AppointmentPortalService.get_doctor_slots(db, uuid.UUID(doctor_id), date)

@router.post("/book")
async def book_appointment(
    db: DBSession, 
    patient_id: str, 
    doctor_id: str, 
    appointment_time: datetime,
    type: AppointmentType = AppointmentType.IN_PERSON,
    reason: str | None = None,
    slot_id: str | None = None
):
    return await AppointmentPortalService.book_appointment(
        db, 
        uuid.UUID(patient_id), 
        uuid.UUID(doctor_id), 
        appointment_time,
        type,
        reason,
        uuid.UUID(slot_id) if slot_id else None
    )
