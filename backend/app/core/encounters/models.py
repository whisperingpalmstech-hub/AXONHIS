"""Encounters module – Encounter model (OPD, IPD, ER visits)."""
import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EncounterType(StrEnum):
    OPD = "OPD"
    IPD = "IPD"
    ER = "ER"


class EncounterStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISCHARGED = "DISCHARGED"
    TRANSFERRED = "TRANSFERRED"
    CANCELLED = "CANCELLED"


class Encounter(Base):
    __tablename__ = "encounters"
    __table_args__ = {'extend_existing': True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    encounter_type: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=True, default=EncounterStatus.ACTIVE
    )
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    encounter_uuid: Mapped[str | None] = mapped_column(String(50), unique=True, index=True, nullable=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False, default="GENERAL")
    
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=True
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

