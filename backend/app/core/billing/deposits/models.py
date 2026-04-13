"""Deposit Management Models for Billing Module."""
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Integer, Numeric, UUID
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid

from app.database import Base


class Deposit(Base):
    """Security deposit, active deposit."""
    __tablename__ = "billing_deposits_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    deposit_type = Column(String(50), nullable=False)  # 'security', 'active'
    deposit_number = Column(String(100), unique=True, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)  # 'cash', 'card', 'upi', 'neft', 'cheque'
    payment_reference = Column(String(200), nullable=True)
    received_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active = Column(Boolean, default=True)
    is_refundable = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)


class DepositUsage(Base):
    """Track deposit usage."""
    __tablename__ = "billing_deposit_usage_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deposit_id = Column(UUID(as_uuid=True), ForeignKey("billing_deposits_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    bill_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    amount_used = Column(Numeric(12, 2), nullable=False)
    used_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    used_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)


class DepositRefund(Base):
    """Refund tracking."""
    __tablename__ = "billing_deposit_refunds_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deposit_id = Column(UUID(as_uuid=True), ForeignKey("billing_deposits_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    refund_amount = Column(Numeric(12, 2), nullable=False)
    refund_method = Column(String(50), nullable=False)  # 'cash', 'card', 'upi', 'neft', 'cheque'
    refund_reference = Column(String(200), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'approved', 'processed', 'rejected'
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class FamilyDeposit(Base):
    """Family deposit with OTP."""
    __tablename__ = "billing_family_deposits_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_deposit_number = Column(String(100), unique=True, nullable=False, index=True)
    primary_patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    available_amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_reference = Column(String(200), nullable=True)
    received_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)


class FamilyDepositMember(Base):
    """Family deposit members."""
    __tablename__ = "billing_family_deposit_members_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_deposit_id = Column(UUID(as_uuid=True), ForeignKey("billing_family_deposits_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    relationship = Column(String(50), nullable=False)  # 'self', 'spouse', 'child', 'parent', 'sibling'
    is_active = Column(Boolean, default=True)
    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class FamilyDepositOTP(Base):
    """OTP for family deposit usage."""
    __tablename__ = "billing_family_deposit_otps_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_deposit_id = Column(UUID(as_uuid=True), ForeignKey("billing_family_deposits_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    otp_code = Column(String(10), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
