import uuid
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from decimal import Decimal


# ── Batch Usage ────────────────────────────────────────────────────────
class IPTargetBatchOut(BaseModel):
    batch_id: uuid.UUID
    batch_number: str
    quantity_deducted: float
    class Config:
        from_attributes = True

class IPTargetBatchCreate(BaseModel):
    batch_id: uuid.UUID
    batch_number: str
    quantity_deducted: float


# ── Items ──────────────────────────────────────────────────────────────
class IPDispenseRecordCreate(BaseModel):
    drug_id: Optional[uuid.UUID] = None
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    prescribed_quantity: float
    is_non_formulary: bool = False
    store_id: Optional[uuid.UUID] = None
    store_name: str = "Main Pharmacy"


class IPDispenseRecordOut(BaseModel):
    id: uuid.UUID
    issue_id: uuid.UUID
    drug_id: Optional[uuid.UUID]
    medication_name: str
    dosage: Optional[str]
    frequency: Optional[str]
    route: Optional[str]
    prescribed_quantity: float
    dispensed_quantity: float
    instructions: Optional[str]
    status: str
    is_non_formulary: bool
    substituted_for: Optional[str]
    store_id: Optional[uuid.UUID]
    store_name: Optional[str]
    batches: List[IPTargetBatchOut] = []
    class Config:
        from_attributes = True


# ── Master Issue ───────────────────────────────────────────────────────
class IPPendingIssueCreate(BaseModel):
    patient_id: Optional[uuid.UUID] = None
    patient_name: str
    uhid: str
    admission_number: str
    ward: Optional[str] = None
    bed_number: Optional[str] = None
    treating_doctor_name: Optional[str] = None
    source: str
    priority: str = "Routine"
    items: List[IPDispenseRecordCreate]


class IPPendingIssueOut(BaseModel):
    id: uuid.UUID
    patient_id: Optional[uuid.UUID]
    patient_name: str
    uhid: str
    admission_number: str
    ward: Optional[str]
    bed_number: Optional[str]
    treating_doctor_name: Optional[str]
    source: str
    priority: str
    status: str
    order_date: datetime
    created_at: datetime
    items: List[IPDispenseRecordOut] = []
    class Config:
        from_attributes = True


# ── Dispense Submission ────────────────────────────────────────────────
class IPDispenseItemSubmission(BaseModel):
    record_id: uuid.UUID
    drug_id: Optional[uuid.UUID] = None
    medication_name: str
    dispensed_quantity: float
    instructions: Optional[str] = None
    substituted_for: Optional[str] = None
    unit_price: float = 0.0  # For IPD billing (manual input for non-formulary, auto otherwise)
    batches: List[IPTargetBatchCreate]


class IPDispenseSubmission(BaseModel):
    items: List[IPDispenseItemSubmission]


# ── Log & Billing ──────────────────────────────────────────────────────
class IPOrderLogOut(BaseModel):
    id: uuid.UUID
    pharmacist_id: uuid.UUID
    action_type: str
    details: dict
    timestamp: datetime
    class Config:
        from_attributes = True

class IPBillingRecordOut(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    charge_amount: float
    billed_at: datetime
    billing_synced: bool
    class Config:
        from_attributes = True
