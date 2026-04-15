import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TransfusionStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    STOPPED = "stopped"


class Transfusion(Base):
    __tablename__ = "transfusions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    blood_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("blood_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transfusion_start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    transfusion_end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    administered_by: Mapped[str] = mapped_column(String(255), nullable=False)
    supervised_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transfusion_status: Mapped[str] = mapped_column(String(50), default=TransfusionStatus.IN_PROGRESS, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    patient = relationship("Patient", primaryjoin="Transfusion.patient_id == Patient.id")
    encounter = relationship("Encounter", primaryjoin="Transfusion.encounter_id == Encounter.id")
    blood_unit = relationship("BloodUnit", primaryjoin="Transfusion.blood_unit_id == BloodUnit.id")
