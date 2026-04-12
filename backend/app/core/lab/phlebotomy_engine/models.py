"""
LIS Phlebotomy & Sample Collection Engine – Database Models

Tables:
  lis_phlebotomy_worklist      – pending collections queue
  lis_sample_collection        – collected sample records
  lis_consent_documents        – consent forms for tests
  lis_repeat_sample_schedule   – multi-sample schedules (GTT etc.)
  lis_sample_transport         – transport tracking to Central Receiving
  lis_phlebotomy_audit         – immutable audit trail
"""
import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import (
    DateTime, ForeignKey, String, Text, Boolean, Integer, Float
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ── Enumerations ─────────────────────────────────────────────────────────────

class SampleCollectionStatus(StrEnum):
    PENDING_COLLECTION = "PENDING_COLLECTION"
    COLLECTED = "COLLECTED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED_IN_LAB = "RECEIVED_IN_LAB"
    PROCESSING = "PROCESSING"
    REJECTED = "REJECTED"


class CollectionLocation(StrEnum):
    OPD = "OPD"
    IPD = "IPD"
    EMERGENCY = "EMERGENCY"
    HOME = "HOME"
    BEDSIDE = "BEDSIDE"
    PHLEBOTOMY_CENTER = "PHLEBOTOMY_CENTER"


class CollectionPriority(StrEnum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    STAT = "STAT"


class ContainerType(StrEnum):
    EDTA_TUBE = "EDTA_TUBE"
    PLAIN_TUBE = "PLAIN_TUBE"
    CITRATE_TUBE = "CITRATE_TUBE"
    HEPARIN_TUBE = "HEPARIN_TUBE"
    FLUORIDE_TUBE = "FLUORIDE_TUBE"
    URINE_CUP = "URINE_CUP"
    SWAB_TUBE = "SWAB_TUBE"
    BIOPSY_JAR = "BIOPSY_JAR"
    OTHER = "OTHER"


class TransportStatus(StrEnum):
    DISPATCHED = "DISPATCHED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"


class HomeCollectionStatus(StrEnum):
    REQUESTED = "REQUESTED"
    ASSIGNED = "ASSIGNED"
    EN_ROUTE = "EN_ROUTE"
    COLLECTED = "COLLECTED"
    CANCELLED = "CANCELLED"


# ── 1. Phlebotomy Worklist ────────────────────────────────────────────────────

class PhlebotomyWorklist(Base):
    """Pending sample collection items."""
    __tablename__ = "lis_phlebotomy_worklist"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    order_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    patient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    patient_uhid: Mapped[str | None] = mapped_column(String(50), nullable=True)
    visit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    test_code: Mapped[str] = mapped_column(String(50), nullable=False)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_type: Mapped[str] = mapped_column(String(30), nullable=False, default="BLOOD")
    barcode: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CollectionPriority.ROUTINE, index=True
    )
    collection_location: Mapped[str] = mapped_column(
        String(30), nullable=False, default=CollectionLocation.OPD
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=SampleCollectionStatus.PENDING_COLLECTION, index=True
    )
    consent_required: Mapped[bool] = mapped_column(default=False, nullable=False)
    consent_uploaded: Mapped[bool] = mapped_column(default=False, nullable=False)
    assigned_collector: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scheduled_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_repeat: Mapped[bool] = mapped_column(default=False, nullable=False)
    repeat_schedule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── 2. Sample Collection ─────────────────────────────────────────────────────

class SampleCollection(Base):
    """Completed sample collection records."""
    __tablename__ = "lis_sample_collection"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    worklist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_phlebotomy_worklist.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    sample_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    patient_uhid: Mapped[str | None] = mapped_column(String(50), nullable=True)
    barcode: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    test_code: Mapped[str] = mapped_column(String(50), nullable=False)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_type: Mapped[str] = mapped_column(String(30), nullable=False)
    container_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ContainerType.PLAIN_TUBE
    )
    collection_location: Mapped[str] = mapped_column(
        String(30), nullable=False, default=CollectionLocation.OPD
    )
    collector_name: Mapped[str] = mapped_column(String(255), nullable=False)
    collector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=SampleCollectionStatus.COLLECTED
    )
    identity_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    identity_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity_ml: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Status history
    status_history: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


# ── 3. Consent Documents ─────────────────────────────────────────────────────

class ConsentDocument(Base):
    """Consent documents for tests requiring patient consent."""
    __tablename__ = "lis_consent_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    worklist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_phlebotomy_worklist.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    test_code: Mapped[str] = mapped_column(String(50), nullable=False)
    document_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="CONSENT"
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_format: Mapped[str] = mapped_column(String(10), nullable=False, default="PDF")
    uploaded_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    verified: Mapped[bool] = mapped_column(default=False, nullable=False)


# ── 4. Repeat Sample Schedule ────────────────────────────────────────────────

class RepeatSampleSchedule(Base):
    """Schedule for multi-sample tests (GTT, etc.)."""
    __tablename__ = "lis_repeat_sample_schedule"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    test_code: Mapped[str] = mapped_column(String(50), nullable=False)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_samples: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    collected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    schedule_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_complete: Mapped[bool] = mapped_column(default=False, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── 5. Sample Transport ──────────────────────────────────────────────────────

class SampleTransport(Base):
    """Transport tracking of samples to Central Receiving."""
    __tablename__ = "lis_sample_transport"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    batch_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    sample_ids: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transport_personnel: Mapped[str] = mapped_column(String(255), nullable=False)
    transport_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MANUAL"
    )
    dispatch_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    received_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    received_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=TransportStatus.DISPATCHED
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── 6. Phlebotomy Audit Trail ────────────────────────────────────────────────

class PhlebotomyAudit(Base):
    """Immutable audit trail for all phlebotomy actions."""
    __tablename__ = "lis_phlebotomy_audit"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    performed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
