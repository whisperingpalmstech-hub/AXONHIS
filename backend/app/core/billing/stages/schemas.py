"""Multi-stage Billing Schemas for Billing Module."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PartialPaymentCreate(BaseModel):
    """Schema for creating a partial payment."""
    amount: float
    payment_method: str
    payment_reference: Optional[str] = None
    reason: str


class PartialPaymentResponse(BaseModel):
    """Schema for partial payment response."""
    id: str
    bill_id: str
    amount: float
    payment_method: str
    payment_reference: Optional[str] = None
    reason: str
    received_by: str
    received_at: datetime

    class Config:
        from_attributes = True


class BillHoldCreate(BaseModel):
    """Schema for placing a bill on hold."""
    hold_reason: str
    hold_type: str


class BillHoldResponse(BaseModel):
    """Schema for bill hold response."""
    id: str
    bill_id: str
    hold_reason: str
    hold_type: str
    is_active: bool
    placed_by: str
    placed_at: datetime
    released_at: Optional[datetime] = None
    released_by: Optional[str] = None

    class Config:
        from_attributes = True


class RefundRequestCreate(BaseModel):
    """Schema for creating a refund request."""
    refund_amount: float
    refund_method: str
    reason: str


class RefundRequestResponse(BaseModel):
    """Schema for refund request response."""
    id: str
    bill_id: str
    refund_amount: float
    refund_method: str
    reason: str
    status: str
    requested_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CreditNoteCreate(BaseModel):
    """Schema for creating a credit note."""
    amount: float
    reason: str


class CreditNoteResponse(BaseModel):
    """Schema for credit note response."""
    id: str
    bill_id: Optional[str] = None
    note_number: str
    amount: float
    reason: str
    status: str
    requested_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DebitNoteCreate(BaseModel):
    """Schema for creating a debit note."""
    amount: float
    reason: str


class DebitNoteResponse(BaseModel):
    """Schema for debit note response."""
    id: str
    bill_id: Optional[str] = None
    note_number: str
    amount: float
    reason: str
    status: str
    requested_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
