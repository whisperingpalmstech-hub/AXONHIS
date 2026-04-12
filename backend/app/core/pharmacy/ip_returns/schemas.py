from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from decimal import Decimal

class IPReturnItemCreate(BaseModel):
    dispense_record_id: uuid.UUID
    batch_id: Optional[uuid.UUID] = None
    batch_number: Optional[str] = None
    drug_id: Optional[uuid.UUID] = None
    medication_name: str
    return_quantity: Decimal
    reason: str
    condition: Optional[str] = None
    is_restockable: bool = True

class IPReturnCreate(BaseModel):
    request_type: str = Field(..., description="'Return' or 'Rejection'")
    issue_id: uuid.UUID
    patient_id: Optional[uuid.UUID] = None
    patient_name: str
    uhid: str
    admission_number: str
    ward: Optional[str] = None
    bed_number: Optional[str] = None
    requested_by: str
    items: List[IPReturnItemCreate]

class IPReturnProcess(BaseModel):
    action: str = Field(..., description="'Accept' or 'Reject'")
    remarks: Optional[str] = None
    refund_amount_total: Optional[Decimal] = Field(None, description="Sum of amounts to credit back to IPD bill")

class IPReturnItemOut(BaseModel):
    id: uuid.UUID
    dispense_record_id: uuid.UUID
    batch_id: Optional[uuid.UUID] = None
    batch_number: Optional[str] = None
    drug_id: Optional[uuid.UUID] = None
    medication_name: str
    return_quantity: Decimal
    reason: str
    condition: Optional[str] = None
    is_restockable: bool

    class Config:
        orm_mode = True

class IPReturnOut(BaseModel):
    id: uuid.UUID
    request_type: str
    issue_id: uuid.UUID
    patient_id: Optional[uuid.UUID] = None
    patient_name: str
    uhid: str
    admission_number: str
    ward: Optional[str] = None
    bed_number: Optional[str] = None
    status: str
    requested_by: str
    request_date: datetime
    processed_by: Optional[uuid.UUID] = None
    processed_date: Optional[datetime] = None
    remarks: Optional[str] = None
    items: List[IPReturnItemOut]

    class Config:
        orm_mode = True

class IPReturnLogOut(BaseModel):
    id: uuid.UUID
    action_type: str
    details: dict
    timestamp: datetime

    class Config:
        orm_mode = True
