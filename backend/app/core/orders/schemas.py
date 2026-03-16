"""Order schemas."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    item_type: str
    item_id: uuid.UUID | None = None
    item_name: str
    quantity: float = 1.0
    unit: str | None = None
    dose: str | None = None
    frequency: str | None = None
    route: str | None = None
    unit_price: float = 0.0
    instructions: str | None = None


class OrderCreate(BaseModel):
    encounter_id: uuid.UUID
    patient_id: uuid.UUID
    order_type: str
    priority: str = "ROUTINE"
    notes: str | None = None
    metadata_: dict[str, Any] = Field(default_factory=dict)
    items: list[OrderItemCreate] = Field(default_factory=list)


class OrderItemOut(BaseModel):
    id: uuid.UUID
    item_type: str
    item_name: str
    quantity: float
    unit: str | None
    dose: str | None
    frequency: str | None
    route: str | None
    unit_price: float
    instructions: str | None

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: uuid.UUID
    encounter_id: uuid.UUID
    patient_id: uuid.UUID
    order_type: str
    status: str
    priority: str
    ordered_by: uuid.UUID
    approved_by: uuid.UUID | None
    notes: str | None
    items: list[OrderItemOut]
    created_at: datetime
    approved_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class OrderApprove(BaseModel):
    notes: str | None = None


class OrderCancel(BaseModel):
    reason: str = Field(min_length=5)
