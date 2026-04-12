import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class PharmacyIPPendingIssue(Base):
    """Master record for an inpatient medication order."""
    __tablename__ = "pharmacy_ip_pending_issues"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Patient & IPD info
    patient_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    patient_name = Column(String(200), nullable=False)
    uhid = Column(String(50), nullable=False, index=True)
    admission_number = Column(String(50), nullable=False, index=True)
    ward = Column(String(100), nullable=True)
    bed_number = Column(String(50), nullable=True)
    treating_doctor_name = Column(String(200), nullable=True)
    # Order metadata
    source = Column(String(50), nullable=False)  # e.g., "Doctor Desk", "Nursing Station"
    priority = Column(String(50), default="Routine")  # Urgent, STAT, Routine
    status = Column(String(50), nullable=False, default="Pending")  # Pending, In Progress, Dispensed, Completed
    order_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    items = relationship("PharmacyIPDispenseRecord", back_populates="pending_issue", cascade="all, delete-orphan")
    logs = relationship("PharmacyIPOrderLog", back_populates="pending_issue", cascade="all, delete-orphan")
    billing = relationship("PharmacyIPBillingRecord", back_populates="pending_issue", cascade="all, delete-orphan")


class PharmacyIPDispenseRecord(Base):
    """Medications to be dispensed for a single IP order."""
    __tablename__ = "pharmacy_ip_dispense_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_ip_pending_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    # Target medication
    drug_id = Column(UUID(as_uuid=True), nullable=True)
    medication_name = Column(String(255), nullable=False)
    # Prescribed instructions
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    route = Column(String(100), nullable=True)
    prescribed_quantity = Column(Numeric(12, 2), nullable=False)
    # Dispensing
    dispensed_quantity = Column(Numeric(12, 2), nullable=False, default=0)
    instructions = Column(String(500), nullable=True)
    status = Column(String(50), default="Pending")
    # Sub & Non-Formulary
    is_non_formulary = Column(Boolean, default=False)
    substituted_for = Column(String(255), nullable=True)
    # Target store
    store_id = Column(UUID(as_uuid=True), nullable=True)
    store_name = Column(String(100), default="Main Pharmacy")

    pending_issue = relationship("PharmacyIPPendingIssue", back_populates="items")
    batches = relationship("PharmacyIPDispenseBatch", back_populates="dispense_record", cascade="all, delete-orphan")


class PharmacyIPDispenseBatch(Base):
    """Inventory batches used to fulfill the IP issue."""
    __tablename__ = "pharmacy_ip_dispense_batches"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispense_record_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_ip_dispense_records.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = Column(UUID(as_uuid=True), nullable=False)
    batch_number = Column(String(100), nullable=False)
    quantity_deducted = Column(Numeric(12, 2), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    dispense_record = relationship("PharmacyIPDispenseRecord", back_populates="batches")


class PharmacyIPBillingRecord(Base):
    """Charges sent to IPD billing."""
    __tablename__ = "pharmacy_ip_billing_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_ip_pending_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_ip_dispense_records.id", ondelete="CASCADE"), nullable=False)
    charge_amount = Column(Numeric(12, 2), nullable=False)
    billed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    billing_synced = Column(Boolean, default=False)
    
    pending_issue = relationship("PharmacyIPPendingIssue", back_populates="billing")


class PharmacyIPOrderLog(Base):
    """Immutable audit trail for IP issues."""
    __tablename__ = "pharmacy_ip_order_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_ip_pending_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    pharmacist_id = Column(UUID(as_uuid=True), nullable=False)
    action_type = Column(String(100), nullable=False)
    details = Column(JSONB, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    pending_issue = relationship("PharmacyIPPendingIssue", back_populates="logs")
