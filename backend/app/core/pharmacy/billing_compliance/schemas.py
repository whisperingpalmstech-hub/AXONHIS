from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# Base Models
class BillingItem(BaseModel):
    drug_id: str
    quantity: float
    unit_price: float
    tax: float
    discount_val: float = 0.0

# 1. Billing Transaction Schemas
class BillingRecordCreate(BaseModel):
    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    billing_type: str = Field(description="OP_WALKIN, OP_PRESCRIPTION, IP_DISCHARGE")
    bill_items: List[BillingItem]

class BillingRecordOut(BaseModel):
    id: UUID
    patient_id: Optional[UUID]
    encounter_id: Optional[UUID]
    bill_number: str
    billing_type: str
    total_amount: float
    tax_amount: float
    discount_amount: float
    net_payable: float
    payment_status: str
    created_at: datetime
    bill_items: List[dict]

    model_config = ConfigDict(from_attributes=True)

# 2. Discount & Concession Schemas
class DiscountCreate(BaseModel):
    bill_id: UUID
    discount_type: str = Field(description="HOSPITAL, DOCTOR, STAFF, PROMO")
    discount_mode: str = Field(description="PERCENTAGE, FIXED")
    discount_value: float
    reason: str

class DiscountOut(BaseModel):
    id: UUID
    bill_id: UUID
    discount_type: str
    discount_mode: str
    discount_value: float
    approved_amount: float
    authorized_by: Optional[UUID]
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 3. Payment Processing Schemas
class PaymentCreate(BaseModel):
    bill_id: UUID
    amount_paid: float
    payment_mode: str = Field(description="CASH, CREDIT_CARD, DEBIT_CARD, UPI, NET_BANKING, INSURANCE")
    transaction_reference: Optional[str] = None

class PaymentOut(BaseModel):
    id: UUID
    bill_id: UUID
    receipt_number: str
    amount_paid: float
    payment_mode: str
    transaction_reference: Optional[str]
    status: str
    transaction_date: datetime

    model_config = ConfigDict(from_attributes=True)

# 4. Refund Schemas
class RefundCreate(BaseModel):
    bill_id: UUID
    transaction_id: Optional[UUID] = None
    refund_amount: float
    refund_mode: str = Field(description="CASH, BANK_TRANSFER, CREDIT_NOTE")
    refund_reason: str

class RefundOut(BaseModel):
    id: UUID
    bill_id: UUID
    refund_amount: float
    refund_mode: str
    refund_reason: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 5. Reporting Schemas
class ReportGenerate(BaseModel):
    report_type: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ReportOut(BaseModel):
    id: UUID
    report_type: str
    report_date: Optional[datetime]
    data_payload: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
