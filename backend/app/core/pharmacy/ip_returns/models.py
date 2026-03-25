import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, JSON, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class PharmacyIPReturn(Base):
    __tablename__ = "pharmacy_ip_returns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_type = Column(String(50), nullable=False) # "Return" or "Rejection"
    issue_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_ip_pending_issues.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    patient_name = Column(String(255), nullable=False)
    uhid = Column(String(100), index=True, nullable=False)
    admission_number = Column(String(100), index=True, nullable=False)
    ward = Column(String(100), nullable=True)
    bed_number = Column(String(100), nullable=True)
    status = Column(String(50), default="Pending") # Pending, Accepted, Rejected
    requested_by = Column(String(100), nullable=False) # e.g. Nurse Name
    request_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_by = Column(UUID(as_uuid=True), nullable=True) # Pharmacist ID
    processed_date = Column(DateTime(timezone=True), nullable=True)
    remarks = Column(Text, nullable=True)

    items = relationship("PharmacyIPReturnItem", back_populates="return_request", cascade="all, delete-orphan")
    logs = relationship("PharmacyIPReturnLog", back_populates="return_request", cascade="all, delete-orphan")
    billing_adjustments = relationship("PharmacyIPBillingAdjustment", back_populates="return_request", cascade="all, delete-orphan")
    issue = relationship("PharmacyIPPendingIssue") # References previous module

class PharmacyIPReturnItem(Base):
    __tablename__ = "pharmacy_ip_return_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    return_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_ip_returns.id"), nullable=False, index=True)
    dispense_record_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_ip_dispense_records.id"), nullable=False, index=True)
    batch_id = Column(UUID(as_uuid=True), nullable=True)
    batch_number = Column(String(100), nullable=True)
    drug_id = Column(UUID(as_uuid=True), nullable=True)
    medication_name = Column(String(255), nullable=False)
    return_quantity = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(255), nullable=False) # e.g., "wrong medication", "discontinued", "adverse drug reaction"
    condition = Column(String(100), nullable=True) # e.g., "Intact", "Damaged"
    is_restockable = Column(Boolean, default=True)

    return_request = relationship("PharmacyIPReturn", back_populates="items")
    dispense_record = relationship("PharmacyIPDispenseRecord")

class PharmacyIPBillingAdjustment(Base):
    __tablename__ = "pharmacy_ip_billing_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    return_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_ip_returns.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=True)
    admission_number = Column(String(100), nullable=False)
    adjustment_amount = Column(Numeric(10, 2), nullable=False)
    adjustment_type = Column(String(50), nullable=False, default="Credit")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    return_request = relationship("PharmacyIPReturn", back_populates="billing_adjustments")

class PharmacyIPReturnLog(Base):
    __tablename__ = "pharmacy_ip_return_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    return_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_ip_returns.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    action_type = Column(String(100), nullable=False) # e.g. "Draft", "Accepted", "Rejected"
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    return_request = relationship("PharmacyIPReturn", back_populates="logs")
