from typing import Sequence
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.patients.appointments.models import Appointment
from app.core.patients.appointments.schemas import AppointmentCreate, AppointmentUpdate

class AppointmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def schedule_appointment(self, patient_id: uuid.UUID, data: AppointmentCreate) -> Appointment:
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=data.doctor_id,
            department=data.department,
            appointment_time=data.appointment_time,
            status=data.status
        )
        self.db.add(appointment)
        await self.db.flush()
        return appointment

    async def get_appointment(self, appointment_id: uuid.UUID) -> Appointment | None:
        stmt = select(Appointment).where(Appointment.id == appointment_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_appointment(self, appointment: Appointment, data: AppointmentUpdate) -> Appointment:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(appointment, key, value)
        await self.db.flush()
        return appointment

    async def list_patient_appointments(self, patient_id: uuid.UUID) -> Sequence[Appointment]:
        stmt = select(Appointment).where(Appointment.patient_id == patient_id).order_by(Appointment.appointment_time.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()
