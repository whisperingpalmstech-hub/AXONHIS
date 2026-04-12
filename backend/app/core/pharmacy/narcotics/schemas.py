from pydantic import BaseModel, Field
from typing import List, Optional, Any
import uuid
from datetime import datetime
from decimal import Decimal

class NarcoticsOrderCreate(BaseModel):
    patient_id: Optional[uuid.UUID] = None
    patient_name: str
    uhid: str
    admission_number: str
    ward: Optional[str] = None
    bed_number: Optional[str] = None
    prescribing_doctor: str
    
    drug_id: Optional[uuid.UUID] = None
    medication_name: str
    dosage: Optional[str] = None
    requested_quantity: Decimal

class NarcoticsValidation(BaseModel):
    action: str = Field(..., description="'Approve' or 'Reject'")
    remarks: Optional[str] = None

class NarcoticsDispensation(BaseModel):
    batch_id: Optional[uuid.UUID] = None
    batch_number: str
    dispensed_quantity: Decimal

class NarcoticsDelivery(BaseModel):
    nurse_name: str
    handover_notes: Optional[str] = None

class AmpouleReturnCreate(BaseModel):
    dispense_id: Optional[uuid.UUID] = None
    medication_name: str
    returned_quantity: Decimal
    returned_by_nurse: str
    notes: Optional[str] = None

class AmpouleVerification(BaseModel):
    verified_by_pharmacist: uuid.UUID
    notes: Optional[str] = None

class NarcoticsDispenseOut(BaseModel):
    id: uuid.UUID
    batch_id: Optional[uuid.UUID] = None
    batch_number: str
    dispensed_quantity: Decimal
    dispensing_time: datetime
    dispensed_by: Optional[uuid.UUID] = None

    class Config:
        orm_mode = True

class AmpouleReturnOut(BaseModel):
    id: uuid.UUID
    dispense_id: Optional[uuid.UUID] = None
    medication_name: str
    returned_quantity: Decimal
    returned_by_nurse: str
    return_date: datetime
    verified_by_pharmacist: Optional[uuid.UUID] = None
    verification_date: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        orm_mode = True

class NarcoticsAuditLogOut(BaseModel):
    id: uuid.UUID
    action_type: str
    details: dict
    timestamp: datetime

    class Config:
        orm_mode = True

class NarcoticsOrderOut(BaseModel):
    id: uuid.UUID
    patient_id: Optional[uuid.UUID] = None
    patient_name: str
    uhid: str
    admission_number: str
    ward: Optional[str] = None
    bed_number: Optional[str] = None
    prescribing_doctor: str
    drug_id: Optional[uuid.UUID] = None
    medication_name: str
    dosage: Optional[str] = None
    requested_quantity: Decimal
    order_date: datetime
    status: str
    is_narcotics: bool
    validated_by: Optional[uuid.UUID] = None
    validation_date: Optional[datetime] = None
    validation_remarks: Optional[str] = None
    nurse_name: Optional[str] = None
    delivery_time: Optional[datetime] = None
    handover_notes: Optional[str] = None
    
    dispenses: List[NarcoticsDispenseOut] = []
    returns: List[AmpouleReturnOut] = []

    class Config:
        orm_mode = True

class NarcoticsInventoryOut(BaseModel):
    id: uuid.UUID
    drug_id: Optional[uuid.UUID] = None
    medication_name: str
    batch_id: Optional[uuid.UUID] = None
    batch_number: str
    stock_quantity: Decimal
    expiry_date: Optional[datetime] = None
    last_updated: datetime

    class Config:
        orm_mode = True
