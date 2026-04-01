"""Integration Schemas"""
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class ChargePostingCreate(BaseModel):
    patient_id: UUID
    encounter_type: str  # er, opd, ipd
    encounter_id: UUID
    service_name: str
    service_code: Optional[str] = None
    service_id: Optional[UUID] = None
    service_group: Optional[str] = None
    source_module: str  # pharmacy, lab, radiology, procedure, consultation, bed, nursing
    source_order_id: Optional[UUID] = None
    quantity: int = 1
    unit_price: Decimal
    is_stat: bool = False

class ChargePostingOut(BaseModel):
    id: UUID; org_id: UUID; patient_id: UUID; encounter_type: str; encounter_id: UUID
    service_name: str; service_code: Optional[str]; source_module: str
    quantity: int; unit_price: Decimal; discount_amount: Decimal; tax_amount: Decimal
    net_amount: Decimal; is_stat: bool; is_billed: bool; posted_by_name: Optional[str]
    posted_at: datetime
    class Config: from_attributes = True

class PatientLedgerOut(BaseModel):
    id: UUID; org_id: UUID; patient_id: UUID; encounter_type: str; encounter_id: UUID
    total_charges: Decimal; total_discounts: Decimal; total_tax: Decimal
    total_deposits: Decimal; total_payments: Decimal; total_insurance_covered: Decimal
    outstanding_balance: Decimal; last_updated: datetime
    class Config: from_attributes = True

class ERToIPDTransferRequest(BaseModel):
    er_encounter_id: UUID
    department: str
    bed_category: Optional[str] = None
    attending_doctor: Optional[str] = None

class CrossModuleEventOut(BaseModel):
    id: UUID; org_id: UUID; event_type: str; source_module: str; target_module: str
    source_id: UUID; target_id: Optional[UUID]; status: str; triggered_at: datetime
    class Config: from_attributes = True

class PatientBillSummary(BaseModel):
    patient_id: UUID
    encounter_type: str
    encounter_id: UUID
    charges: List[ChargePostingOut] = []
    ledger: Optional[PatientLedgerOut] = None
    total_unbilled: Decimal = Decimal("0")
