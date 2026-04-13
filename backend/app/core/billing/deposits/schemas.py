"""Deposit Management Schemas for Billing Module."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DepositCreate(BaseModel):
    """Schema for creating a deposit."""
    patient_id: str
    deposit_type: str  # 'security', 'active'
    amount: float
    payment_method: str  # 'cash', 'card', 'upi', 'neft', 'cheque'
    payment_reference: Optional[str] = None
    is_refundable: bool = True
    notes: Optional[str] = None


class DepositResponse(BaseModel):
    """Schema for deposit response."""
    id: str
    patient_id: str
    deposit_type: str
    deposit_number: str
    amount: float
    payment_method: str
    payment_reference: Optional[str] = None
    received_by: str
    received_at: datetime
    is_active: bool
    is_refundable: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class DepositRefundCreate(BaseModel):
    """Schema for creating a refund request."""
    refund_amount: float
    refund_method: str  # 'cash', 'card', 'upi', 'neft', 'cheque'
    refund_reference: Optional[str] = None
    reason: str


class DepositRefundResponse(BaseModel):
    """Schema for refund response."""
    id: str
    deposit_id: str
    refund_amount: float
    refund_method: str
    refund_reference: Optional[str] = None
    reason: str
    status: str
    requested_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FamilyDepositCreate(BaseModel):
    """Schema for creating a family deposit."""
    primary_patient_id: str
    total_amount: float
    payment_method: str
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


class FamilyDepositMemberCreate(BaseModel):
    """Schema for adding a member to family deposit."""
    patient_id: str
    relationship: str  # 'self', 'spouse', 'child', 'parent', 'sibling'


class FamilyDepositOTPValidate(BaseModel):
    """Schema for validating family deposit OTP."""
    family_deposit_id: str
    patient_id: str
    otp_code: str
