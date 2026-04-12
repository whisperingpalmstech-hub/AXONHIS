import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

class SaleItemCreate(BaseModel):
    drug_id: uuid.UUID
    batch_id: uuid.UUID
    quantity: Decimal
    unit_price: Decimal
    dosage_instructions: Optional[str] = None
    substituted_for_id: Optional[uuid.UUID] = None

class SaleItemOut(SaleItemCreate):
    id: uuid.UUID
    total_price: Decimal
    model_config = ConfigDict(from_attributes=True)

class SalePaymentCreate(BaseModel):
    payment_mode: str
    amount_paid: Decimal
    transaction_ref: Optional[str] = None

class SalePaymentOut(SalePaymentCreate):
    id: uuid.UUID
    payment_date: datetime
    model_config = ConfigDict(from_attributes=True)

class SaleCreate(BaseModel):
    patient_id: Optional[uuid.UUID] = None
    walkin_name: Optional[str] = None
    walkin_mobile: Optional[str] = None
    walkin_age: Optional[str] = None
    walkin_gender: Optional[str] = None
    walkin_address: Optional[str] = None
    prescriber_name: Optional[str] = None
    items: List[SaleItemCreate]
    discount_amount: Decimal = Decimal('0.0')

class SaleOut(BaseModel):
    id: uuid.UUID
    patient_id: Optional[uuid.UUID] = None
    walkin_name: Optional[str] = None
    walkin_mobile: Optional[str] = None
    walkin_age: Optional[str] = None
    walkin_gender: Optional[str] = None
    walkin_address: Optional[str] = None
    prescriber_name: Optional[str] = None
    pharmacist_id: uuid.UUID
    sale_date: datetime
    total_amount: Decimal
    discount_amount: Decimal
    net_amount: Decimal
    status: str
    items: List[SaleItemOut] = []
    payment: Optional[SalePaymentOut] = None
    model_config = ConfigDict(from_attributes=True)

class PrescriptionUploadCreate(BaseModel):
    file_url: str
    extracted_text: Optional[str] = None
    doctor_name: Optional[str] = None
    requires_validation: bool = True

class PrescriptionUploadOut(PrescriptionUploadCreate):
    id: uuid.UUID
    sale_id: Optional[uuid.UUID] = None
    model_config = ConfigDict(from_attributes=True)

class KitAddRequest(BaseModel):
    kit_name: str
    # Pre-defined mock kit names map to a set of item generic names
