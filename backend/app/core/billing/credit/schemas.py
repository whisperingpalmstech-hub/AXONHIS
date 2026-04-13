"""Credit Patient Billing Schemas for Billing Module."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CreditCompanyCreate(BaseModel):
    """Schema for creating a credit company."""
    company_name: str
    company_code: str
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True


class AuthorizationCreate(BaseModel):
    """Schema for creating an authorization."""
    patient_id: str
    contract_id: str
    authorized_amount: float
    valid_from: datetime
    valid_to: Optional[datetime] = None


class AuthorizationResponse(BaseModel):
    """Schema for authorization response."""
    id: str
    authorization_number: str
    patient_id: str
    contract_id: str
    authorized_amount: float
    used_amount: float
    status: str
    valid_from: datetime
    valid_to: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CoPaySplitCreate(BaseModel):
    """Schema for creating a co-pay split."""
    bill_id: str
    patient_id: str
    contract_id: Optional[str] = None
    total_amount: float
    copay_percentage: Optional[float] = None


class DenialCreate(BaseModel):
    """Schema for creating a denial."""
    bill_id: str
    service_id: str
    service_name: str
    denial_reason: str
    denial_code: Optional[str] = None
    denied_amount: float


class InvoiceCreate(BaseModel):
    """Schema for creating an invoice."""
    contract_id: str
    patient_id: str
    bill_ids: List[str]
    due_date: Optional[datetime] = None


class InvoiceSettlementCreate(BaseModel):
    """Schema for creating an invoice settlement."""
    settlement_amount: float
    settlement_method: str  # 'cheque', 'neft', 'upi', 'card'
    settlement_reference: Optional[str] = None
    notes: Optional[str] = None
