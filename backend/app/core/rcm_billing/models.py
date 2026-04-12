"""Enterprise OPD Billing & Revenue Cycle Engine Models"""
import uuid
from datetime import datetime
from enum import StrEnum
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer, Numeric,
    ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class BillStatus(StrEnum):
    draft = "draft"
    unpaid = "unpaid"
    partially_paid = "partially_paid"
    paid = "paid"
    cancelled = "cancelled"
    refunded = "refunded"

class PayerType(StrEnum):
    self_pay = "self_pay"
    insurance = "insurance"
    corporate = "corporate"

class BillingMaster(Base):
    """Central invoice heading for a patient visit"""
    __tablename__ = "rcm_billing_master"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    
    bill_number = Column(String(50), unique=True, nullable=False)
    status = Column(String(30), default=BillStatus.unpaid)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    gross_amount = Column(Numeric(10, 2), default=0.00)
    discount_amount = Column(Numeric(10, 2), default=0.00)
    net_amount = Column(Numeric(10, 2), default=0.00)
    paid_amount = Column(Numeric(10, 2), default=0.00)
    balance_amount = Column(Numeric(10, 2), default=0.00)
    
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    generated_by = Column(UUID(as_uuid=True), nullable=False)

class BillingService(Base):
    """Line items on a bill (Consultation, Labs, Procedures)"""
    __tablename__ = "rcm_billing_services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("rcm_billing_master.id"), nullable=False)
    
    service_name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)
    sub_department = Column(String(100), nullable=True)
    
    base_rate = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, default=1)
    total_cost = Column(Numeric(10, 2), nullable=False)
    
    is_auto_billed = Column(Boolean, default=False)
    status = Column(String(30), default="active") # active, cancelled
    
    added_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class BillingPayment(Base):
    """Ledger of payments mapping to a master bill"""
    __tablename__ = "rcm_billing_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("rcm_billing_master.id"), nullable=False)
    
    payment_mode = Column(String(50), nullable=False) # cash, card, bank_transfer, online
    amount = Column(Numeric(10, 2), nullable=False)
    transaction_reference = Column(String(255), nullable=True)
    
    collected_by = Column(UUID(as_uuid=True), nullable=False)
    collected_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class BillingDiscount(Base):
    """Rule-based discount / concession logs"""
    __tablename__ = "rcm_billing_discounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("rcm_billing_master.id"), nullable=False)
    
    discount_type = Column(String(50), nullable=False) # fixed, percentage, senior_citizen, employee
    discount_value = Column(Numeric(10, 2), nullable=False) # absolute amount deduced
    reason = Column(Text, nullable=True)
    
    authorized_by = Column(UUID(as_uuid=True), nullable=False)
    applied_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class BillingRefund(Base):
    """Audit trail of refunded or reversed charges"""
    __tablename__ = "rcm_billing_refunds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("rcm_billing_master.id"), nullable=False)
    payment_id = Column(UUID(as_uuid=True), nullable=True) # if reversing a specific payment
    
    refund_amount = Column(Numeric(10, 2), nullable=False)
    refund_mode = Column(String(50), nullable=False) # cash, online_reversal
    reason = Column(String(255), nullable=False)
    
    authorized_by = Column(UUID(as_uuid=True), nullable=False)
    refunded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class BillingPayer(Base):
    """Identifies the guarantor of a bill (Insurance Co., Employer, etc.)"""
    __tablename__ = "rcm_billing_payers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("rcm_billing_master.id"), nullable=False)
    
    payer_type = Column(String(50), default=PayerType.self_pay)
    insurance_provider = Column(String(255), nullable=True)
    policy_number = Column(String(255), nullable=True)
    authorization_status = Column(String(50), nullable=True) # pending, approved, rejected
    
    corporate_employer = Column(String(255), nullable=True)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
class BillingTariff(Base):
    """Internal Reference Dictionary for Service Computations based on grade/sponsor."""
    __tablename__ = "rcm_billing_tariffs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String(255), nullable=False)
    
    tariff_category = Column(String(100), nullable=False) # standard, corporate, insurance
    doctor_grade = Column(String(50), nullable=True) # junior, senior, specialist
    
    price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
