from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from .models import BillStatus, PayerType

# ── 3. Billing Tariffs ───────────────────────────────────────────

class TariffMatchQuery(BaseModel):
    service_name: str
    patient_category: str = "standard"
    doctor_grade: Optional[str] = None
    insurance_plan: Optional[str] = None

class BillingTariffOut(BaseModel):
    id: UUID
    service_name: str
    tariff_category: str
    doctor_grade: Optional[str]
    price: Decimal

    class Config: from_attributes = True

# ── 2. Billing Services ──────────────────────────────────────────

class BillingServiceCreate(BaseModel):
    service_name: str
    department: Optional[str] = None
    sub_department: Optional[str] = None
    quantity: int = 1
    is_auto_billed: bool = False
    base_rate: Optional[Decimal] = None # Filled securely via API unless overridden admin

class BillingServiceOut(BillingServiceCreate):
    id: UUID
    bill_id: UUID
    base_rate: Decimal
    total_cost: Decimal
    added_at: datetime
    status: str
    class Config: from_attributes = True

# ── 4. Billing Payer ──────────────────────────────────────────────

class BillingPayerCreate(BaseModel):
    payer_type: PayerType = PayerType.self_pay
    insurance_provider: Optional[str] = None
    policy_number: Optional[str] = None
    authorization_status: Optional[str] = None
    corporate_employer: Optional[str] = None

class BillingPayerOut(BillingPayerCreate):
    id: UUID
    bill_id: UUID
    class Config: from_attributes = True

# ── 5. Billing Discounts ──────────────────────────────────────────

class BillingDiscountCreate(BaseModel):
    discount_type: str = "percentage"
    discount_value: Decimal = Decimal("0.00")
    reason: Optional[str] = None

class BillingDiscountOut(BillingDiscountCreate):
    id: UUID
    bill_id: UUID
    authorized_by: UUID
    applied_at: datetime
    class Config: from_attributes = True

# ── 6. Billing Payments ───────────────────────────────────────────

class BillingPaymentCreate(BaseModel):
    payment_mode: str
    amount: Decimal
    transaction_reference: Optional[str] = None

class BillingPaymentOut(BillingPaymentCreate):
    id: UUID
    bill_id: UUID
    collected_by: UUID
    collected_at: datetime
    class Config: from_attributes = True

# ── 9. Refunds ───────────────────────────────────────────────────
class BillingRefundCreate(BaseModel):
    payment_id: Optional[UUID] = None
    refund_amount: Decimal
    refund_mode: str
    reason: str

class BillingRefundOut(BillingRefundCreate):
    id: UUID
    bill_id: UUID
    authorized_by: UUID
    refunded_at: datetime
    class Config: from_attributes = True

# ── 1. & 8. Master Bill (Pre-Consult & Global) ────────────────────

class BillingPreviewOut(BaseModel):
    estimated_cost: Decimal
    service_name: str
    tariff_applied: str

class BillingMasterCreate(BaseModel):
    visit_id: UUID
    patient_id: UUID
    services: List[BillingServiceCreate]
    payer: BillingPayerCreate

class BillingMasterOut(BaseModel):
    id: UUID
    visit_id: UUID
    patient_id: UUID
    bill_number: str
    status: BillStatus
    gross_amount: Decimal
    discount_amount: Decimal
    net_amount: Decimal
    paid_amount: Decimal
    balance_amount: Decimal
    generated_at: datetime
    settled_at: Optional[datetime]
    
    services: List[BillingServiceOut] = []
    payments: List[BillingPaymentOut] = []
    discounts: List[BillingDiscountOut] = []
    payer: Optional[BillingPayerOut] = None

    class Config: from_attributes = True
