"""Contract Management Models for Billing Module."""
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Integer, Numeric, UUID
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid

from app.database import Base


class Contract(Base):
    """Corporate/Insurance contracts."""
    __tablename__ = "billing_contracts_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_number = Column(String(100), unique=True, nullable=False, index=True)
    contract_name = Column(String(200), nullable=False)
    contract_type = Column(String(50), nullable=False)  # 'corporate', 'insurance', 'government'
    company_name = Column(String(200), nullable=False)
    contact_person = Column(String(200), nullable=True)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    terms = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ContractInclusion(Base):
    """Services included in contract."""
    __tablename__ = "billing_contract_inclusions_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_contracts_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(UUID(as_uuid=True), nullable=False)
    service_name = Column(String(200), nullable=False)
    service_type = Column(String(50), nullable=False)  # 'hospital_service', 'lab', 'radiology', 'pharmacy'
    is_mandatory = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ContractExclusion(Base):
    """Services excluded from contract."""
    __tablename__ = "billing_contract_exclusions_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_contracts_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(UUID(as_uuid=True), nullable=False)
    service_name = Column(String(200), nullable=False)
    service_type = Column(String(50), nullable=False)
    exclusion_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ContractCoPay(Base):
    """Co-pay configuration for contracts."""
    __tablename__ = "billing_contract_copay_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_contracts_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    service_type = Column(String(50), nullable=True)  # Null means applies to all services
    copay_type = Column(String(50), nullable=False)  # 'percentage', 'fixed', 'tiered'
    copay_value = Column(Numeric(12, 2), nullable=False)
    copay_percentage = Column(Numeric(5, 2), nullable=True)
    min_copay = Column(Numeric(12, 2), nullable=True)
    max_copay = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ContractCAP(Base):
    """CAP amount configuration for contracts."""
    __tablename__ = "billing_contract_caps_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_contracts_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    cap_type = Column(String(50), nullable=False)  # 'per_visit', 'per_month', 'per_year', 'lifetime'
    cap_amount = Column(Numeric(12, 2), nullable=False)
    cap_period_start = Column(DateTime(timezone=True), nullable=True)
    cap_period_end = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ContractCreditLimit(Base):
    """Credit limit configuration for contracts."""
    __tablename__ = "billing_contract_credit_limits_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_contracts_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    credit_limit = Column(Numeric(12, 2), nullable=False)
    used_credit = Column(Numeric(12, 2), nullable=False, default=0)
    available_credit = Column(Numeric(12, 2), nullable=False)
    reset_period = Column(String(50), nullable=True)  # 'monthly', 'quarterly', 'yearly'
    last_reset_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ContractPaymentTerms(Base):
    """Payment terms for contracts."""
    __tablename__ = "billing_contract_payment_terms_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_contracts_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_mode = Column(String(50), nullable=False)  # 'credit', 'prepaid', 'postpaid'
    credit_period_days = Column(Integer, nullable=True)
    discount_for_early_payment = Column(Numeric(5, 2), nullable=True)  # Percentage
    early_payment_days = Column(Integer, nullable=True)
    penalty_for_late_payment = Column(Numeric(5, 2), nullable=True)  # Percentage
    late_payment_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ContractPackage(Base):
    """Packages under contract."""
    __tablename__ = "billing_contract_packages_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_contracts_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    package_id = Column(UUID(as_uuid=True), nullable=False)
    package_name = Column(String(200), nullable=False)
    contract_price = Column(Numeric(12, 2), nullable=False)  # Special price under contract
    is_mandatory = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ContractEmployeeGrade(Base):
    """Employee grade contracts."""
    __tablename__ = "billing_contract_employee_grades_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_contracts_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_grade = Column(String(50), nullable=False)  # 'A', 'B', 'C', 'executive', 'staff'
    discount_percentage = Column(Numeric(5, 2), nullable=False)
    credit_limit = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class PatientCreditAssignment(Base):
    """Patient to credit company assignment."""
    __tablename__ = "billing_patient_credit_assignments_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_contracts_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(String(100), nullable=True)
    employee_grade = Column(String(50), nullable=True)
    assigned_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active = Column(Boolean, default=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
