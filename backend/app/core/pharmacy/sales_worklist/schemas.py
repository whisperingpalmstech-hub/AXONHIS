import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class PharmacyPrescriptionBase(BaseModel):
    drug_id: Optional[uuid.UUID] = None
    medication_name: str
    dosage_instructions: Optional[str] = None
    quantity_prescribed: float
    doctor_notes: Optional[str] = None
    is_non_formulary: bool = False
    substituted_for: Optional[str] = None

class PharmacyPrescriptionOut(PharmacyPrescriptionBase):
    id: uuid.UUID
    worklist_id: uuid.UUID
    class Config:
        from_attributes = True

class PharmacySalesWorklistBase(BaseModel):
    patient_id: Optional[uuid.UUID] = None
    patient_name: str
    uhid: str
    visit_id: Optional[uuid.UUID] = None
    doctor_name: str
    prescription_id: uuid.UUID

class PharmacySalesWorklistOut(PharmacySalesWorklistBase):
    id: uuid.UUID
    status: str
    prescription_date: datetime
    created_at: datetime
    prescriptions: List[PharmacyPrescriptionOut] = []
    class Config:
        from_attributes = True

class DispenseBatchCreate(BaseModel):
    batch_id: uuid.UUID
    batch_number: str
    quantity: float
    expiry_date: Optional[datetime] = None

class DispenseRequestItem(BaseModel):
    prescription_id: uuid.UUID
    drug_id: Optional[uuid.UUID] = None
    medication_name: str
    quantity_dispensed: float
    dosage_instructions: Optional[str] = None
    unit_price: float = 0.0
    is_non_formulary: bool = False
    substituted_for: Optional[str] = None # original medication_name if substituted
    batches: List[DispenseBatchCreate] = []

class DispenseRequest(BaseModel):
    items: List[DispenseRequestItem]
    pharmacist_id: str # typically from auth but can be passed
    billing_transaction_id: Optional[str] = None

class PharmacyDispenseLogOut(BaseModel):
    id: uuid.UUID
    worklist_id: uuid.UUID
    pharmacist_id: uuid.UUID
    action_type: str
    details: dict
    timestamp: datetime
    class Config:
        from_attributes = True
