from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .models import TransfusionPriority, AllocationStatus


# --- Transfusion Order Schemas ---
class TransfusionOrderBase(BaseModel):
    order_id: UUID | None = None
    patient_id: UUID
    encounter_id: UUID | None = None
    requested_component_id: UUID
    units_requested: int
    priority: TransfusionPriority = TransfusionPriority.ROUTINE


class TransfusionOrderCreate(TransfusionOrderBase):
    pass


class TransfusionOrderUpdate(BaseModel):
    order_status: str | None = None


class TransfusionOrderResponse(TransfusionOrderBase):
    id: UUID
    order_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Blood Allocation Schemas ---
class BloodAllocationBase(BaseModel):
    transfusion_order_id: UUID
    blood_unit_id: UUID
    allocated_by: str


class BloodAllocationCreate(BloodAllocationBase):
    pass


class BloodAllocationUpdate(BaseModel):
    allocation_status: AllocationStatus | None = None


class BloodAllocationResponse(BloodAllocationBase):
    id: UUID
    allocated_at: datetime
    allocation_status: AllocationStatus

    class Config:
        from_attributes = True
