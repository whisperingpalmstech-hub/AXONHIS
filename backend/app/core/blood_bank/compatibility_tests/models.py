import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CompatibilityResult(StrEnum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    PENDING = "pending"


class CrossmatchTest(Base):
    __tablename__ = "crossmatch_tests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    blood_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("blood_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_blood_group: Mapped[str] = mapped_column(String(10), nullable=False)
    unit_blood_group: Mapped[str] = mapped_column(String(10), nullable=False)
    compatibility_result: Mapped[str] = mapped_column(String(50), default=CompatibilityResult.PENDING, nullable=False)
    tested_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    patient = relationship("Patient", primaryjoin="CrossmatchTest.patient_id == Patient.id")
    blood_unit = relationship("BloodUnit", primaryjoin="CrossmatchTest.blood_unit_id == BloodUnit.id")
