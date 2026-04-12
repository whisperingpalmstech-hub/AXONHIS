import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class PharmacySalesReturn(Base):
    """Master return transaction record."""
    __tablename__ = "pharmacy_sales_returns"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    return_number = Column(String(50), unique=True, nullable=False, index=True)
    # Link to original sale
    sale_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    worklist_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    bill_number = Column(String(100), nullable=True, index=True)
    # Patient info
    patient_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    patient_name = Column(String(200), nullable=True)
    uhid = Column(String(50), nullable=True)
    mobile = Column(String(20), nullable=True)
    # Pharmacist
    pharmacist_id = Column(UUID(as_uuid=True), nullable=True)
    pharmacist_name = Column(String(200), nullable=True)
    # Financials
    total_refund_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    discount_adjustment = Column(Numeric(12, 2), nullable=False, default=0.0)
    tax_adjustment = Column(Numeric(12, 2), nullable=False, default=0.0)
    net_refund = Column(Numeric(12, 2), nullable=False, default=0.0)
    # Status
    status = Column(String(50), nullable=False, default="Pending")  # Pending, Approved, Completed, Rejected
    sale_date = Column(DateTime(timezone=True), nullable=True)
    return_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    items = relationship("PharmacyReturnItem", back_populates="sales_return", cascade="all, delete-orphan")
    refund = relationship("PharmacyReturnRefund", back_populates="sales_return", uselist=False, cascade="all, delete-orphan")


class PharmacyReturnItem(Base):
    """Individual medications being returned."""
    __tablename__ = "pharmacy_return_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    return_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_sales_returns.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_id = Column(UUID(as_uuid=True), nullable=True)
    medication_name = Column(String(255), nullable=False)
    batch_id = Column(UUID(as_uuid=True), nullable=True)
    batch_number = Column(String(100), nullable=True)
    quantity_sold = Column(Numeric(12, 2), nullable=False)
    quantity_returned = Column(Numeric(12, 2), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    refund_amount = Column(Numeric(12, 2), nullable=False)
    # Return reason
    reason_id = Column(UUID(as_uuid=True), nullable=True)
    reason_text = Column(String(255), nullable=True)
    # Eligibility
    is_eligible = Column(Boolean, default=True, nullable=False)
    eligibility_note = Column(String(500), nullable=True)
    # Stock reconciliation
    stock_restored = Column(Boolean, default=False, nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)

    sales_return = relationship("PharmacySalesReturn", back_populates="items")


class PharmacyReturnReason(Base):
    """Predefined return reasons for compliance."""
    __tablename__ = "pharmacy_return_reasons"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reason_code = Column(String(50), unique=True, nullable=False)
    reason_text = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    requires_approval = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class PharmacyReturnRefund(Base):
    """Refund transaction linked to a return."""
    __tablename__ = "pharmacy_return_refunds"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    return_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_sales_returns.id", ondelete="CASCADE"), nullable=False, unique=True)
    refund_amount = Column(Numeric(12, 2), nullable=False)
    refund_mode = Column(String(50), nullable=False, default="Cash")  # Cash, Card, UPI, Wallet
    transaction_ref = Column(String(100), nullable=True)
    refunded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    refunded_by = Column(UUID(as_uuid=True), nullable=True)

    sales_return = relationship("PharmacySalesReturn", back_populates="refund")


class PharmacyReturnLog(Base):
    """Immutable audit trail for return transactions."""
    __tablename__ = "pharmacy_return_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    return_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    pharmacist_id = Column(UUID(as_uuid=True), nullable=True)
    action_type = Column(String(100), nullable=False)
    details = Column(JSONB, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
