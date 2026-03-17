import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

class InventoryItemCreate(BaseModel):
    drug_id: uuid.UUID
    quantity_available: float = 0.0
    reorder_threshold: float = 10.0

class InventoryItemUpdate(BaseModel):
    quantity_available: float
    reason: str = "adjustment"

class InventoryItemOut(InventoryItemCreate):
    id: uuid.UUID
    last_updated: datetime
    model_config = ConfigDict(from_attributes=True)
