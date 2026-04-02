import uuid
from datetime import datetime, date, time
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .models import PortalAppointment, DoctorAvailability, AppointmentType, AppointmentStatus
from app.core.auth.models import User

class AppointmentPortalService:
    @staticmethod
    async def get_available_doctors(db: AsyncSession, patient_id: uuid.UUID, department: str | None = None):
        """Fetch all doctors with their availability."""
        # Dynamic import to avoid circular dependencies
        from app.core.patients.patients.models import Patient
        from app.core.auth.models import Role, UserRole
        
        patient = await db.scalar(select(Patient).where(Patient.id == patient_id))
        
        # If the org lacks an org_id (e.g. test patients), don't filter by org_id strictly
        query = (
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(Role.name == "doctor")
        )
        
        if patient and patient.org_id:
            query = query.where(User.org_id == patient.org_id)
        
        if department:
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
    async def get_doctor_slots(db: AsyncSession, doctor_id: uuid.UUID, slot_date: date):
        from app.core.scheduling.models import CalendarSlot, SlotStatus
        query = select(CalendarSlot).where(
            and_(
                CalendarSlot.doctor_id == doctor_id,
                CalendarSlot.slot_date == slot_date,
                CalendarSlot.status == SlotStatus.AVAILABLE
            )
        ).order_by(CalendarSlot.start_time)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def book_appointment(
        db: AsyncSession, 
        patient_id: uuid.UUID, 
        doctor_id: uuid.UUID, 
        appointment_time: datetime,
        type: AppointmentType,
        reason: str | None = None,
        slot_id: uuid.UUID | None = None
    ):
        """Action for booking a new appointment from the portal."""
        try:
            appointment = PortalAppointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                department="General Practice",
                appointment_time=appointment_time,
                appointment_type=type,
                status=AppointmentStatus.SCHEDULED
            )
            db.add(appointment)
            
            # Auto-sync with Main Hospital Scheduling Module (Appointments list)
            from app.core.patients.appointments.models import Appointment as HospitalAppointment
            hospital_apt = HospitalAppointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                department="General Practice",
                appointment_time=appointment_time.replace(tzinfo=None),
                status="scheduled"
            )
            db.add(hospital_apt)
            
            # Auto-sync directly to the Scheduler Grid if they picked a slot
            if slot_id:
                from app.core.scheduling.models import SlotBooking, CalendarSlot, SlotStatus
                
                # Fetch slot and decrease availability
                slot = await db.scalar(select(CalendarSlot).where(CalendarSlot.id == slot_id))
                if slot and slot.status == SlotStatus.AVAILABLE:
                    slot_booking = SlotBooking(
                        slot_id=slot_id,
                        patient_id=patient_id,
                        doctor_id=doctor_id,
                        department="General Practice",
                        booking_date=slot.slot_date,
                        appointment_type=type,
                        status="confirmed",
                        reason=reason
                    )
                    slot.current_bookings += 1
                    if slot.current_bookings >= slot.max_bookings:
                        slot.status = SlotStatus.BOOKED
                    db.add(slot_booking)
            
            await db.commit()
            await db.refresh(appointment)
            return appointment
        except Exception as e:
            await db.rollback()
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"Failed to book appointment: {str(e)}")

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
