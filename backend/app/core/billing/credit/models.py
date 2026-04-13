"""Credit Patient Billing Models for Billing Module."""
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Integer, Numeric, UUID
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid

from app.database import Base


class CreditCompany(Base):
    """Credit company details."""
    __tablename__ = "billing_credit_companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(200), nullable=False)
    company_code = Column(String(50), unique=True, nullable=False, index=True)
    contact_person = Column(String(200), nullable=True)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PatientCreditAssignment(Base):
    """Patient to credit company assignment (reused from contracts)."""
    __tablename__ = "billing_patient_credit_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(String(100), nullable=True)
    employee_grade = Column(String(50), nullable=True)
    assigned_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active = Column(Boolean, default=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class Authorization(Base):
    """Authorization tracking."""
    __tablename__ = "billing_authorizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    authorization_number = Column(String(100), unique=True, nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    authorized_amount = Column(Numeric(12, 2), nullable=False)
    used_amount = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(50), nullable=False, default="active")  # 'active', 'exhausted', 'expired', 'cancelled'
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class CoPaySplit(Base):
    """Co-pay splitting tracking."""
    __tablename__ = "billing_copay_splits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_contracts.id", ondelete="SET NULL"), nullable=True, index=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    patient_share = Column(Numeric(12, 2), nullable=False)
    company_share = Column(Numeric(12, 2), nullable=False)
    copay_percentage = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Denial(Base):
    """Denial tracking."""
    __tablename__ = "billing_denials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    service_id = Column(UUID(as_uuid=True), nullable=False)
    service_name = Column(String(200), nullable=False)
    denial_reason = Column(Text, nullable=False)
    denial_code = Column(String(50), nullable=True)
    denied_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'approved', 'rejected'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class Invoice(Base):
    """Invoice generation for credit billing."""
    __tablename__ = "billing_invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_contracts.id", ondelete="SET NULL"), nullable=True, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    bill_ids = Column(JSONB, nullable=True)  # List of bill IDs
    total_amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'sent', 'partial', 'settled', 'overdue', 'cancelled'
    due_date = Column(DateTime(timezone=True), nullable=True)
    sent_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class InvoiceSettlement(Base):
    """Invoice settlement tracking."""
    __tablename__ = "billing_invoice_settlements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("billing_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    settlement_amount = Column(Numeric(12, 2), nullable=False)
    settlement_method = Column(String(50), nullable=False)  # 'cheque', 'neft', 'upi', 'card'
    settlement_reference = Column(String(200), nullable=True)
    settlement_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
