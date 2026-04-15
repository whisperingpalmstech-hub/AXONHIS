import uuid
from datetime import datetime, timezone
from enum import StrEnum
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SurgeryPriority(StrEnum):
    ELECTIVE = "elective"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class SurgeryStatus(StrEnum):
    SCHEDULED = "scheduled"
    PREPARING = "preparing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SurgerySchedule(Base):
    __tablename__ = "surgery_schedule"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    procedure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("surgical_procedures.id", ondelete="CASCADE"), nullable=False, index=True
    )
    operating_room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operating_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scheduled_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default=SurgeryPriority.ELECTIVE, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=SurgeryStatus.SCHEDULED, nullable=False)
    scheduled_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    patient = relationship("Patient", primaryjoin="SurgerySchedule.patient_id == Patient.id", foreign_keys=[patient_id])
    encounter = relationship("Encounter", primaryjoin="SurgerySchedule.encounter_id == Encounter.id", foreign_keys=[encounter_id])
    procedure = relationship("SurgicalProcedure")
    operating_room = relationship("OperatingRoom")
    team = relationship("SurgicalTeam", back_populates="schedule", uselist=False)
    anesthesia_record = relationship("AnesthesiaRecord", back_populates="schedule", uselist=False)
    events = relationship("SurgeryEvent", back_populates="schedule")
    notes = relationship("SurgeryNote", back_populates="schedule")
    postoperative_events = relationship("PostoperativeEvent", back_populates="schedule")

    def __repr__(self) -> str:
        return f"<SurgerySchedule id={self.id} patient={self.patient_id} status={self.status}>"
