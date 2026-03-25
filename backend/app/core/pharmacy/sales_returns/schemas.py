import uuid
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from decimal import Decimal


# ── Return Reasons ─────────────────────────────────────────────────────
class ReturnReasonOut(BaseModel):
    id: uuid.UUID
    reason_code: str
    reason_text: str
    is_active: bool
    requires_approval: bool
    class Config:
        from_attributes = True


# ── Return Items ───────────────────────────────────────────────────────
class ReturnItemCreate(BaseModel):
    drug_id: Optional[uuid.UUID] = None
    medication_name: str
    batch_id: Optional[uuid.UUID] = None
    batch_number: Optional[str] = None
    quantity_sold: float
    quantity_returned: float
    unit_price: float
    reason_text: str = "Unused medication"


class ReturnItemOut(BaseModel):
    id: uuid.UUID
    medication_name: str
    batch_number: Optional[str]
    quantity_sold: float
    quantity_returned: float
    unit_price: float
    refund_amount: float
    reason_text: Optional[str]
    is_eligible: bool
    eligibility_note: Optional[str]
    stock_restored: bool
    class Config:
        from_attributes = True


# ── Refund ─────────────────────────────────────────────────────────────
class RefundOut(BaseModel):
    id: uuid.UUID
    refund_amount: float
    refund_mode: str
    transaction_ref: Optional[str]
    refunded_at: datetime
    class Config:
        from_attributes = True


# ── Sales Return Master ───────────────────────────────────────────────
class SalesReturnCreate(BaseModel):
    sale_id: Optional[uuid.UUID] = None
    worklist_id: Optional[uuid.UUID] = None
    bill_number: Optional[str] = None
    patient_name: str
    uhid: str = ""
    mobile: str = ""
    sale_date: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[ReturnItemCreate]


class SalesReturnOut(BaseModel):
    id: uuid.UUID
    return_number: str
    sale_id: Optional[uuid.UUID]
    bill_number: Optional[str]
    patient_name: Optional[str]
    uhid: Optional[str]
    mobile: Optional[str]
    pharmacist_name: Optional[str]
    total_refund_amount: float
    net_refund: float
    status: str
    sale_date: Optional[datetime]
    return_date: datetime
    notes: Optional[str]
    created_at: datetime
    items: List[ReturnItemOut] = []
    refund: Optional[RefundOut] = None
    class Config:
        from_attributes = True


# ── Process Refund ─────────────────────────────────────────────────────
class ProcessRefundRequest(BaseModel):
    refund_mode: str = "Cash"
    transaction_ref: Optional[str] = None


# ── Audit Log ──────────────────────────────────────────────────────────
class ReturnLogOut(BaseModel):
    id: uuid.UUID
    return_id: uuid.UUID
    pharmacist_id: Optional[uuid.UUID]
    action_type: str
    details: dict
    timestamp: datetime
    class Config:
        from_attributes = True


# ── Bill Search Result ─────────────────────────────────────────────────
class BillSearchResult(BaseModel):
    id: str
    bill_number: str
    patient_name: str
    uhid: str
    sale_date: datetime
    total_amount: float
    status: str
    items: list
