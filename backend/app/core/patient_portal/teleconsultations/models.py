import uuid
from datetime import datetime, timezone
from enum import StrEnum
from sqlalchemy import String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TeleconsultationStatus(StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Teleconsultation(Base):
    __tablename__ = "teleconsultations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False, unique=True)
    meeting_link: Mapped[str] = mapped_column(String(500), nullable=False)
    session_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    session_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=TeleconsultationStatus.SCHEDULED.value)
    chat_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    appointment = relationship("Appointment", backref="teleconsultation", uselist=False)
