"""
LIS Laboratory Processing & Result Entry Engine – Database Models

Tables:
  lis_processing_worklist  – samples awaiting processing per department
  lis_result_entry         – test result records (numeric, text, qualitative)
  lis_result_flag          – abnormal/critical result flags
  lis_delta_check          – delta comparisons with previous results
  lis_qc_result            – quality control sample results
  lis_result_comment       – technician remarks & interpretation notes
  lis_processing_audit     – immutable audit trail
"""
import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import (
    DateTime, ForeignKey, String, Text, Boolean, Integer, Float
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ── Enumerations ─────────────────────────────────────────────────────────────

class ProcessingStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESULT_ENTERED = "RESULT_ENTERED"
    AWAITING_VALIDATION = "AWAITING_VALIDATION"
    VALIDATED = "VALIDATED"
    RELEASED = "RELEASED"
    REJECTED = "REJECTED"


class ResultType(StrEnum):
    NUMERIC = "NUMERIC"
    TEXT = "TEXT"
    QUALITATIVE = "QUALITATIVE"
    IMAGE = "IMAGE"


class FlagType(StrEnum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    LOW = "LOW"
    CRITICAL_HIGH = "CRITICAL_HIGH"
    CRITICAL_LOW = "CRITICAL_LOW"
    ABNORMAL = "ABNORMAL"


class ResultSource(StrEnum):
    MANUAL = "MANUAL"
    ANALYZER_HL7 = "ANALYZER_HL7"
    ANALYZER_ASTM = "ANALYZER_ASTM"
    BATCH_IMPORT = "BATCH_IMPORT"


class QCStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    PENDING = "PENDING"


class LabDepartment(StrEnum):
    BIOCHEMISTRY = "BIOCHEMISTRY"
    HEMATOLOGY = "HEMATOLOGY"
    CLINICAL_PATHOLOGY = "CLINICAL_PATHOLOGY"
    SEROLOGY = "SEROLOGY"
    MICROBIOLOGY = "MICROBIOLOGY"
    HISTOPATHOLOGY = "HISTOPATHOLOGY"
    IMMUNOLOGY = "IMMUNOLOGY"
    MOLECULAR_BIOLOGY = "MOLECULAR_BIOLOGY"
    CYTOLOGY = "CYTOLOGY"
    URINALYSIS = "URINALYSIS"


# ── Reference Ranges (configurable seed) ─────────────────────────────────────

REFERENCE_RANGES: dict[str, dict] = {
    "HB": {"unit": "g/dL", "low": 12.0, "high": 16.0, "crit_low": 7.0, "crit_high": 20.0},
    "CBC": {"unit": "cells/mcL", "low": 4500, "high": 11000, "crit_low": 2000, "crit_high": 30000},
    "FBS": {"unit": "mg/dL", "low": 70, "high": 110, "crit_low": 40, "crit_high": 500},
    "LIPID": {"unit": "mg/dL", "low": 0, "high": 200, "crit_low": 0, "crit_high": 500},
    "LFT": {"unit": "U/L", "low": 7, "high": 56, "crit_low": 0, "crit_high": 1000},
    "KFT": {"unit": "mg/dL", "low": 0.6, "high": 1.2, "crit_low": 0, "crit_high": 10},
    "HBA1C": {"unit": "%", "low": 4.0, "high": 5.6, "crit_low": 0, "crit_high": 15},
    "THYROID": {"unit": "mIU/L", "low": 0.4, "high": 4.0, "crit_low": 0, "crit_high": 100},
    "CRP": {"unit": "mg/L", "low": 0, "high": 10, "crit_low": 0, "crit_high": 200},
    "ESR": {"unit": "mm/hr", "low": 0, "high": 20, "crit_low": 0, "crit_high": 100},
    "VITD": {"unit": "ng/mL", "low": 30, "high": 100, "crit_low": 5, "crit_high": 150},
    "VITB12": {"unit": "pg/mL", "low": 200, "high": 900, "crit_low": 100, "crit_high": 2000},
    "TROP": {"unit": "ng/mL", "low": 0, "high": 0.04, "crit_low": 0, "crit_high": 10},
    "URINE_RE": {"unit": "", "low": 0, "high": 0, "crit_low": 0, "crit_high": 0},
}

# Delta thresholds (% change considered significant)
DELTA_THRESHOLDS: dict[str, float] = {
    "HB": 20.0, "CBC": 30.0, "FBS": 30.0, "LFT": 50.0, "KFT": 40.0,
    "HBA1C": 15.0, "THYROID": 40.0, "CRP": 50.0, "ESR": 50.0,
    "TROP": 50.0, "LIPID": 30.0,
}


# ── 1. Processing Worklist ────────────────────────────────────────────────────

class ProcessingWorklist(Base):
    """Samples awaiting processing per lab department."""
    __tablename__ = "lis_processing_worklist"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cr_receipt_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    sample_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    barcode: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    patient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    patient_uhid: Mapped[str | None] = mapped_column(String(50), nullable=True)
    test_code: Mapped[str] = mapped_column(String(50), nullable=False)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_type: Mapped[str] = mapped_column(String(30), nullable=False)
    department: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="ROUTINE", index=True)
    receipt_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_technician: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ProcessingStatus.PENDING, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── 2. Result Entry ───────────────────────────────────────────────────────────

class ResultEntry(Base):
    """Test result records."""
    __tablename__ = "lis_result_entry"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worklist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_processing_worklist.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    sample_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    test_code: Mapped[str] = mapped_column(String(50), nullable=False)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    result_type: Mapped[str] = mapped_column(String(20), nullable=False, default=ResultType.NUMERIC)
    result_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    result_unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reference_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    result_source: Mapped[str] = mapped_column(String(30), nullable=False, default=ResultSource.MANUAL)
    analyzer_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entered_by: Mapped[str] = mapped_column(String(255), nullable=False)
    entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    is_reviewed: Mapped[bool] = mapped_column(default=False, nullable=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ProcessingStatus.RESULT_ENTERED
    )


# ── 3. Result Flags ───────────────────────────────────────────────────────────

class ResultFlag(Base):
    """Abnormal/critical result flags."""
    __tablename__ = "lis_result_flag"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_result_entry.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    flag_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reference_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    result_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_critical: Mapped[bool] = mapped_column(default=False, nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── 4. Delta Checks ──────────────────────────────────────────────────────────

class DeltaCheck(Base):
    """Delta comparisons with previous patient results."""
    __tablename__ = "lis_delta_check"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_result_entry.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    test_code: Mapped[str] = mapped_column(String(50), nullable=False)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    previous_value: Mapped[float] = mapped_column(Float, nullable=False)
    previous_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delta_absolute: Mapped[float] = mapped_column(Float, nullable=False)
    delta_percent: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_percent: Mapped[float] = mapped_column(Float, nullable=False)
    is_significant: Mapped[bool] = mapped_column(default=False, nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── 5. QC Results ─────────────────────────────────────────────────────────────

class QCResult(Base):
    """Quality control sample results."""
    __tablename__ = "lis_qc_result"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    test_code: Mapped[str] = mapped_column(String(50), nullable=False)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    qc_lot_number: Mapped[str] = mapped_column(String(50), nullable=False)
    qc_level: Mapped[str] = mapped_column(String(20), nullable=False, default="NORMAL")
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    expected_sd: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=QCStatus.PENDING)
    analyzer_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    performed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── 6. Result Comments ────────────────────────────────────────────────────────

class ResultComment(Base):
    """Technician remarks and interpretation notes."""
    __tablename__ = "lis_result_comment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_result_entry.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    comment_type: Mapped[str] = mapped_column(String(30), nullable=False, default="REMARK")
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_template: Mapped[bool] = mapped_column(default=False, nullable=False)
    added_by: Mapped[str] = mapped_column(String(255), nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── 7. Processing Audit Trail ────────────────────────────────────────────────

class ProcessingAudit(Base):
    """Immutable audit trail for processing actions."""
    __tablename__ = "lis_processing_audit"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    performed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
