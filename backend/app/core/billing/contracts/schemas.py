"""Contract Management Schemas for Billing Module."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ContractCreate(BaseModel):
    """Schema for creating a contract."""
    contract_number: str
    contract_name: str
    contract_type: str  # 'corporate', 'insurance', 'government'
    company_name: str
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    terms: Optional[str] = None


class ContractUpdate(BaseModel):
    """Schema for updating a contract."""
    contract_name: Optional[str] = None
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    terms: Optional[str] = None


class ContractInclusionCreate(BaseModel):
    """Schema for creating contract inclusion."""
    service_id: str
    service_name: str
    service_type: str
    is_mandatory: bool = False


class ContractExclusionCreate(BaseModel):
    """Schema for creating contract exclusion."""
    service_id: str
    service_name: str
    service_type: str
    exclusion_reason: Optional[str] = None


class ContractCoPayCreate(BaseModel):
    """Schema for creating contract co-pay configuration."""
    service_type: Optional[str] = None
    copay_type: str  # 'percentage', 'fixed', 'tiered'
    copay_value: float
    copay_percentage: Optional[float] = None
    min_copay: Optional[float] = None
    max_copay: Optional[float] = None
    is_active: bool = True


class ContractCAPCreate(BaseModel):
    """Schema for creating contract CAP configuration."""
    cap_type: str  # 'per_visit', 'per_month', 'per_year', 'lifetime'
    cap_amount: float
    cap_period_start: Optional[datetime] = None
    cap_period_end: Optional[datetime] = None
    is_active: bool = True


class ContractCreditLimitCreate(BaseModel):
    """Schema for creating contract credit limit."""
    credit_limit: float
    reset_period: Optional[str] = None  # 'monthly', 'quarterly', 'yearly'
    is_active: bool = True


class ContractPaymentTermsCreate(BaseModel):
    """Schema for creating contract payment terms."""
    payment_mode: str  # 'credit', 'prepaid', 'postpaid'
    credit_period_days: Optional[int] = None
    discount_for_early_payment: Optional[float] = None
    early_payment_days: Optional[int] = None
    penalty_for_late_payment: Optional[float] = None
    late_payment_days: Optional[int] = None
    is_active: bool = True


class ContractPackageCreate(BaseModel):
    """Schema for adding package to contract."""
    package_id: str
    package_name: str
    contract_price: float
    is_mandatory: bool = False


class ContractEmployeeGradeCreate(BaseModel):
    """Schema for creating employee grade contract."""
    employee_grade: str  # 'A', 'B', 'C', 'executive', 'staff'
    discount_percentage: float
    credit_limit: Optional[float] = None
    is_active: bool = True


class PatientCreditAssignmentCreate(BaseModel):
    """Schema for assigning patient to credit company."""
    patient_id: str
    contract_id: str
    employee_id: Optional[str] = None
    employee_grade: Optional[str] = None
