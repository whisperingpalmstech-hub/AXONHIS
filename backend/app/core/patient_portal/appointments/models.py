import uuid
from datetime import datetime, timezone
from enum import StrEnum
from sqlalchemy import String, ForeignKey, DateTime, Date, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AppointmentType(StrEnum):
    IN_PERSON = "in_person"
    TELECONSULTATION = "teleconsultation"


class AppointmentStatus(StrEnum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    available_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    available_time_slot: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)


class PortalAppointment(Base):
    __tablename__ = "portal_appointments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    appointment_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    appointment_type: Mapped[str] = mapped_column(String(50), default=AppointmentType.IN_PERSON.value)
    status: Mapped[str] = mapped_column(String(50), default=AppointmentStatus.SCHEDULED.value, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    patient = relationship("Patient", backref=__import__('sqlalchemy.orm', fromlist=['backref']).backref("portal_appointments_list", cascade="all, delete-orphan"))
    doctor = relationship("User", foreign_keys=[doctor_id], backref="portal_doctor_appointments")
