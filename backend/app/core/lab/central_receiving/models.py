"""
LIS Central Receiving & Specimen Tracking Engine – Database Models

Tables:
  lis_cr_receipt           – sample receipt records at CR
  lis_cr_verification      – quality verification results
  lis_cr_rejection         – rejected sample records
  lis_cr_routing           – department routing assignments
  lis_cr_storage           – temporary sample storage tracking
  lis_cr_chain_of_custody  – full specimen lifecycle tracking
  lis_cr_alert             – missing / overdue sample alerts
  lis_cr_audit             – immutable audit trail
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

class ReceiptStatus(StrEnum):
    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    VERIFIED = "VERIFIED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    ROUTED = "ROUTED"
    STORED = "STORED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class VerificationResult(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    CONDITIONAL = "CONDITIONAL"


class RejectionReason(StrEnum):
    INSUFFICIENT_VOLUME = "INSUFFICIENT_VOLUME"
    INCORRECT_CONTAINER = "INCORRECT_CONTAINER"
    HEMOLYZED = "HEMOLYZED"
    CLOTTED = "CLOTTED"
    LABEL_MISMATCH = "LABEL_MISMATCH"
    TRANSPORT_DELAY = "TRANSPORT_DELAY"
    WRONG_SAMPLE_TYPE = "WRONG_SAMPLE_TYPE"
    CONTAMINATED = "CONTAMINATED"
    EXPIRED = "EXPIRED"
    OTHER = "OTHER"


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


class AlertSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


# ── Test-to-Department Mapping ────────────────────────────────────────────────
TEST_DEPARTMENT_MAP: dict[str, str] = {
    "CBC": LabDepartment.HEMATOLOGY,
    "HB": LabDepartment.HEMATOLOGY,
    "ESR": LabDepartment.HEMATOLOGY,
    "LIPID": LabDepartment.BIOCHEMISTRY,
    "LFT": LabDepartment.BIOCHEMISTRY,
    "KFT": LabDepartment.BIOCHEMISTRY,
    "FBS": LabDepartment.BIOCHEMISTRY,
    "HBA1C": LabDepartment.BIOCHEMISTRY,
    "THYROID": LabDepartment.BIOCHEMISTRY,
    "CRP": LabDepartment.BIOCHEMISTRY,
    "VITD": LabDepartment.BIOCHEMISTRY,
    "VITB12": LabDepartment.BIOCHEMISTRY,
    "TROP": LabDepartment.BIOCHEMISTRY,
    "URINE_RE": LabDepartment.URINALYSIS,
    "ECG": LabDepartment.CLINICAL_PATHOLOGY,
}


# ── 1. CR Receipt ─────────────────────────────────────────────────────────────

class CRReceipt(Base):
    """Sample receipt records at Central Receiving."""
    __tablename__ = "lis_cr_receipt"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    container_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    collection_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collection_location: Mapped[str | None] = mapped_column(String(50), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="ROUTINE", index=True)
    transport_batch_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    received_by: Mapped[str] = mapped_column(String(255), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ReceiptStatus.RECEIVED, index=True
    )
    current_location: Mapped[str] = mapped_column(String(100), nullable=False, default="CENTRAL_RECEIVING")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── 2. CR Verification ────────────────────────────────────────────────────────

class CRVerification(Base):
    """Quality verification results for received samples."""
    __tablename__ = "lis_cr_verification"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_cr_receipt.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    sample_type_correct: Mapped[bool] = mapped_column(default=True, nullable=False)
    container_correct: Mapped[bool] = mapped_column(default=True, nullable=False)
    volume_adequate: Mapped[bool] = mapped_column(default=True, nullable=False)
    labeling_correct: Mapped[bool] = mapped_column(default=True, nullable=False)
    transport_ok: Mapped[bool] = mapped_column(default=True, nullable=False)
    hemolyzed: Mapped[bool] = mapped_column(default=False, nullable=False)
    clotted: Mapped[bool] = mapped_column(default=False, nullable=False)
    overall_result: Mapped[str] = mapped_column(
        String(20), nullable=False, default=VerificationResult.PASS
    )
    verified_by: Mapped[str] = mapped_column(String(255), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── 3. CR Rejection ───────────────────────────────────────────────────────────

class CRRejection(Base):
    """Rejected sample records."""
    __tablename__ = "lis_cr_rejection"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_cr_receipt.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    rejection_reason: Mapped[str] = mapped_column(String(50), nullable=False)
    rejection_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejected_by: Mapped[str] = mapped_column(String(255), nullable=False)
    rejected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    recollection_requested: Mapped[bool] = mapped_column(default=True, nullable=False)
    notification_sent: Mapped[bool] = mapped_column(default=False, nullable=False)
    notification_targets: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


# ── 4. CR Routing ──────────────────────────────────────────────────────────────

class CRRouting(Base):
    """Department routing assignments after acceptance."""
    __tablename__ = "lis_cr_routing"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_cr_receipt.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    target_department: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    routed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    routed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    received_at_dept: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_by_dept: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ROUTED")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── 5. CR Storage ──────────────────────────────────────────────────────────────

class CRStorage(Base):
    """Temporary sample storage tracking."""
    __tablename__ = "lis_cr_storage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_cr_receipt.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    storage_location: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_temperature: Mapped[str] = mapped_column(String(20), nullable=False, default="2-8°C")
    max_duration_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    stored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    stored_by: Mapped[str] = mapped_column(String(255), nullable=False)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    alert_sent: Mapped[bool] = mapped_column(default=False, nullable=False)


# ── 6. Chain of Custody ────────────────────────────────────────────────────────

class CRChainOfCustody(Base):
    """Full specimen lifecycle tracking."""
    __tablename__ = "lis_cr_chain_of_custody"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_cr_receipt.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    sample_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    responsible_staff: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── 7. Alerts ──────────────────────────────────────────────────────────────────

class CRAlert(Base):
    """Missing / overdue sample alerts."""
    __tablename__ = "lis_cr_alert"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default=AlertSeverity.WARNING)
    sample_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    order_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    patient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=AlertStatus.ACTIVE, index=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── 8. Audit Trail ────────────────────────────────────────────────────────────

class CRAudit(Base):
    """Immutable audit trail for CR actions."""
    __tablename__ = "lis_cr_audit"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    performed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
