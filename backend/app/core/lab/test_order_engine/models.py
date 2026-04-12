"""
LIS Test Order Management Engine – Database Models

Tables:
  lis_test_orders          – master test order record
  lis_test_order_items     – individual tests within an order
  lis_test_panels          – predefined test panel/profile templates
  lis_test_panel_items     – tests within a panel
  lis_barcode_registry     – barcode tracking for samples
  lis_order_documents      – uploaded prescriptions / documents
  lis_order_audit_trail    – immutable audit history
"""
import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import (
    DateTime, ForeignKey, String, Text, Boolean, Integer, Float, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ── Enumerations ─────────────────────────────────────────────────────────────

class TestOrderStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    BILLED = "BILLED"
    SAMPLE_COLLECTED = "SAMPLE_COLLECTED"
    IN_PROCESS = "IN_PROCESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TestPriority(StrEnum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    STAT = "STAT"


class SampleType(StrEnum):
    BLOOD = "BLOOD"
    URINE = "URINE"
    TISSUE = "TISSUE"
    SWAB = "SWAB"
    SERUM = "SERUM"
    STOOL = "STOOL"
    CSF = "CSF"
    OTHER = "OTHER"


class OrderSource(StrEnum):
    OPD_BILLING = "OPD_BILLING"
    DOCTOR_DESK = "DOCTOR_DESK"
    IPD_CHARGES = "IPD_CHARGES"
    WALKIN_DIAGNOSTIC = "WALKIN_DIAGNOSTIC"
    PRESCRIPTION_SCAN = "PRESCRIPTION_SCAN"


# ── 1. Test Order Master ─────────────────────────────────────────────────────

class LISTestOrder(Base):
    """Master test order record."""
    __tablename__ = "lis_test_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False, index=True
    )
    visit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    ordering_doctor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department_source: Mapped[str] = mapped_column(
        String(50), nullable=False, default=OrderSource.OPD_BILLING
    )
    order_source: Mapped[str] = mapped_column(
        String(50), nullable=False, default=OrderSource.OPD_BILLING
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TestPriority.ROUTINE, index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=TestOrderStatus.DRAFT, index=True
    )
    clinical_indication: Mapped[str | None] = mapped_column(Text, nullable=True)
    provisional_diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    medication_history: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Insurance/eligibility
    insurance_validated: Mapped[bool] = mapped_column(default=False, nullable=False)
    insurance_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    items: Mapped[list["LISTestOrderItem"]] = relationship(
        "LISTestOrderItem", back_populates="order",
        cascade="all, delete-orphan", lazy="selectin"
    )
    documents: Mapped[list["LISOrderDocument"]] = relationship(
        "LISOrderDocument", back_populates="order",
        cascade="all, delete-orphan", lazy="selectin"
    )
    audit_trail: Mapped[list["LISOrderAuditTrail"]] = relationship(
        "LISOrderAuditTrail", back_populates="order",
        cascade="all, delete-orphan", lazy="selectin"
    )


# ── 2. Test Order Items ──────────────────────────────────────────────────────

class LISTestOrderItem(Base):
    """Individual test within an order."""
    __tablename__ = "lis_test_order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_test_orders.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    test_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default=SampleType.BLOOD
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default=TestPriority.ROUTINE
    )
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=TestOrderStatus.DRAFT
    )
    panel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    barcode: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True, index=True
    )
    collection_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    order: Mapped["LISTestOrder"] = relationship(
        "LISTestOrder", back_populates="items"
    )


# ── 3. Test Panels / Profiles ────────────────────────────────────────────────

class LISTestPanel(Base):
    """Predefined test panel/profile template."""
    __tablename__ = "lis_test_panels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    panel_code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    panel_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    panel_items: Mapped[list["LISTestPanelItem"]] = relationship(
        "LISTestPanelItem", back_populates="panel",
        cascade="all, delete-orphan", lazy="selectin"
    )


class LISTestPanelItem(Base):
    """Individual tests within a panel definition."""
    __tablename__ = "lis_test_panel_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    panel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_test_panels.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    test_code: Mapped[str] = mapped_column(String(50), nullable=False)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default=SampleType.BLOOD
    )
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    panel: Mapped["LISTestPanel"] = relationship(
        "LISTestPanel", back_populates="panel_items"
    )


# ── 5. Barcode Registry ──────────────────────────────────────────────────────

class LISBarcodeRegistry(Base):
    """Barcode tracking for samples."""
    __tablename__ = "lis_barcode_registry"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    barcode: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_test_orders.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    order_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_test_order_items.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    sample_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default=SampleType.BLOOD
    )
    collection_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_collected: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── 6. Order Documents ───────────────────────────────────────────────────────

class LISOrderDocument(Base):
    """Uploaded prescriptions and documents."""
    __tablename__ = "lis_order_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_test_orders.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PRESCRIPTION"
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    ocr_extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_tests: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    order: Mapped["LISTestOrder"] = relationship(
        "LISTestOrder", back_populates="documents"
    )


# ── 9. Order Audit Trail ─────────────────────────────────────────────────────

class LISOrderAuditTrail(Base):
    """Immutable audit history for test orders."""
    __tablename__ = "lis_order_audit_trail"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_test_orders.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    performed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    order: Mapped["LISTestOrder"] = relationship(
        "LISTestOrder", back_populates="audit_trail"
    )
