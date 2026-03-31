"""
Lab module – Complete Laboratory Information System models.

Tables:
  lab_tests      – catalog of available laboratory tests
  lab_samples    – physical sample tracking with barcode
  lab_results    – individual test result entries
  lab_validations – result validation / approval workflow
  lab_processing – analyzer / instrument processing log
"""
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Numeric, String, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ── Enumerations ─────────────────────────────────────────────────────────────

class SampleStatus(StrEnum):
    COLLECTED = "COLLECTED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED_IN_LAB = "RECEIVED_IN_LAB"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class LabOrderStatus(StrEnum):
    PENDING = "PENDING"
    SAMPLE_COLLECTED = "SAMPLE_COLLECTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ResultFlag(StrEnum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    LOW = "LOW"
    CRITICAL_HIGH = "CRITICAL_HIGH"
    CRITICAL_LOW = "CRITICAL_LOW"


class ValidationStatus(StrEnum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


class ProcessingStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ── Lab Test Catalog ─────────────────────────────────────────────────────────

class LabTest(Base):
    """Catalog of available lab tests with reference ranges."""
    __tablename__ = "lab_tests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sample_type: Mapped[str] = mapped_column(String(50), nullable=False, default="blood")
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    normal_range_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    normal_range_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    critical_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    critical_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    turnaround_hours: Mapped[int | None] = mapped_column(nullable=True, default=24)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)


# ── Lab Order (links clinical order to lab workflow) ─────────────────────────

class LabOrder(Base):
    """Links a clinical order (Phase 4) to the lab workflow."""
    __tablename__ = "lab_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=LabOrderStatus.PENDING, index=True
    )
    ordered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)

    # Relationships
    samples: Mapped[list["LabSample"]] = relationship("LabSample", back_populates="lab_order", cascade="all, delete-orphan")


# ── Lab Sample Tracking ──────────────────────────────────────────────────────

class LabSample(Base):
    """Physical sample with barcode tracking."""
    __tablename__ = "lab_samples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lab_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sample_barcode: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    sample_type: Mapped[str] = mapped_column(String(50), nullable=False, default="blood")
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=SampleStatus.COLLECTED, index=True
    )
    collected_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    collection_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    # Relationships
    lab_order: Mapped["LabOrder"] = relationship("LabOrder", back_populates="samples")
    results: Mapped[list["LabResult"]] = relationship("LabResult", back_populates="sample", cascade="all, delete-orphan")
    processing: Mapped[list["LabProcessing"]] = relationship("LabProcessing", back_populates="sample", cascade="all, delete-orphan")


# ── Lab Processing (analyzer integration) ────────────────────────────────────

class LabProcessing(Base):
    """Tracks processing of a sample by analyzers/instruments."""
    __tablename__ = "lab_processing"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lab_samples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analyzer_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ProcessingStatus.QUEUED)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    sample: Mapped["LabSample"] = relationship("LabSample", back_populates="processing")


# ── Lab Results ──────────────────────────────────────────────────────────────

class LabResult(Base):
    """Individual test result entry."""
    __tablename__ = "lab_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lab_samples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lab_tests.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    numeric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reference_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    result_flag: Mapped[str] = mapped_column(String(20), nullable=False, default=ResultFlag.NORMAL)
    is_abnormal: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_critical: Mapped[bool] = mapped_column(default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PRELIMINARY", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    entered_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)

    # Relationships
    sample: Mapped["LabSample"] = relationship("LabSample", back_populates="results")
    validation: Mapped["LabValidation | None"] = relationship("LabValidation", back_populates="result", uselist=False)


# ── Lab Validation ───────────────────────────────────────────────────────────

class LabValidation(Base):
    """Result validation / approval by a lab supervisor."""
    __tablename__ = "lab_validations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lab_results.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    validated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ValidationStatus.PENDING
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)

    result: Mapped["LabResult"] = relationship("LabResult", back_populates="validation")
