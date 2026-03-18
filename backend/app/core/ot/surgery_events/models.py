import uuid
from datetime import datetime, timezone
from enum import StrEnum
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SurgeryEventType(StrEnum):
    PATIENT_IN_ROOM = "patient_in_room"
    ANESTHESIA_STARTED = "anesthesia_started"
    INCISION_MADE = "incision_made"
    PROCEDURE_COMPLETED = "procedure_completed"
    PATIENT_OUT_ROOM = "patient_out_room"


class SurgeryEvent(Base):
    __tablename__ = "surgery_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("surgery_schedule.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    schedule = relationship("SurgerySchedule", back_populates="events")
    recorder = relationship("User")

    def __repr__(self) -> str:
        return f"<SurgeryEvent schedule_id={self.schedule_id} event_type={self.event_type}>"
