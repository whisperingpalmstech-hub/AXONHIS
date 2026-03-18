import uuid
from datetime import datetime, date, time
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .models import PortalAppointment, DoctorAvailability, AppointmentType, AppointmentStatus
from app.core.auth.models import User

class AppointmentPortalService:
    @staticmethod
    async def get_available_doctors(db: AsyncSession, department: str | None = None):
        """Fetch all doctors with their availability."""
        query = select(User).join(User.user_roles).join(__import__('app.core.auth.models').Role).where(__import__('app.core.auth.models').Role.name == "doctor")
        if department:
            # Note: This depends on how department is stored for users.
            # For now, let's just get all doctors.
            pass
        
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_doctor_availability(db: AsyncSession, doctor_id: uuid.UUID, start_date: date, end_date: date):
        """Fetch a specific doctor's availability for a date range."""
        query = select(DoctorAvailability).where(
            and_(
                DoctorAvailability.doctor_id == doctor_id,
                DoctorAvailability.available_date >= start_date,
                DoctorAvailability.available_date <= end_date,
                DoctorAvailability.is_booked == False
            )
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def book_appointment(
        db: AsyncSession, 
        patient_id: uuid.UUID, 
        doctor_id: uuid.UUID, 
        appointment_time: datetime,
        type: AppointmentType,
        reason: str | None = None
    ):
        """Action for booking a new appointment from the portal."""
        # Note: Check if the slot is still available if using a slot system.
        
        appointment = PortalAppointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_time=appointment_time,
            appointment_type=type,
            status=AppointmentStatus.PENDING,
            reason=reason
        )
        db.add(appointment)
        await db.flush()
        return appointment

    @staticmethod
    async def get_patient_appointments(db: AsyncSession, patient_id: uuid.UUID):
        """Fetch all appointments for the patient."""
        query = (
            select(PortalAppointment)
            .where(PortalAppointment.patient_id == patient_id)
            .options(joinedload(PortalAppointment.doctor))
            .order_by(PortalAppointment.appointment_time.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()
