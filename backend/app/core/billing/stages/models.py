"""Multi-stage Billing Models for Billing Module."""
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Integer, Numeric, UUID
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid

from app.database import Base


class BillStage(Base):
    """Bill stage tracking (interim, intermediate, final)."""
    __tablename__ = "billing_bill_stages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("billing_bills.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_type = Column(String(50), nullable=False)  # 'interim', 'intermediate', 'final'
    previous_stage_id = Column(UUID(as_uuid=True), ForeignKey("billing_bill_stages.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class BillStageTransition(Base):
    """Track bill stage changes."""
    __tablename__ = "billing_bill_stage_transitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("billing_bills.id", ondelete="CASCADE"), nullable=False, index=True)
    from_stage = Column(String(50), nullable=True)
    to_stage = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    transitioned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    transitioned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class PartialPayment(Base):
    """Track partial payments on bills."""
    __tablename__ = "billing_partial_payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("billing_bills.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)  # 'cash', 'card', 'upi', 'neft', 'cheque'
    payment_reference = Column(String(200), nullable=True)
    reason = Column(Text, nullable=True)
    received_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class BillHold(Base):
    """Track bills on hold status."""
    __tablename__ = "billing_bill_holds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("billing_bills.id", ondelete="CASCADE"), nullable=False, index=True)
    hold_reason = Column(Text, nullable=False)
    hold_type = Column(String(50), nullable=False)  # 'partial_payment', 'cancellation', 'refund_pending'
    is_active = Column(Boolean, default=True)
    placed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    placed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    released_at = Column(DateTime(timezone=True), nullable=True)
    released_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class RefundRequest(Base):
    """Track refund requests."""
    __tablename__ = "billing_refund_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("billing_bills.id", ondelete="CASCADE"), nullable=False, index=True)
    refund_amount = Column(Numeric(12, 2), nullable=False)
    refund_method = Column(String(50), nullable=False)  # 'cash', 'card', 'upi', 'neft', 'cheque'
    reason = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'approved', 'rejected', 'processed'
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class CreditNote(Base):
    """Track credit notes for post-bill discounts."""
    __tablename__ = "billing_credit_notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("billing_bills.id", ondelete="SET NULL"), nullable=True, index=True)
    note_number = Column(String(100), unique=True, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'approved', 'rejected'
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class DebitNote(Base):
    """Track debit notes for additional charges."""
    __tablename__ = "billing_debit_notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("billing_bills.id", ondelete="SET NULL"), nullable=True, index=True)
    note_number = Column(String(100), unique=True, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'approved', 'rejected'
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
