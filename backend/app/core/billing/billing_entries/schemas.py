from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from typing import Optional
class BillingEntryCreate(BaseModel):
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
    order_id: Optional[uuid.UUID] = None
    service_id: uuid.UUID
    quantity: float = 1.0
    unit_price: float
class BillingEntryOut(BillingEntryCreate):
    id: uuid.UUID
    total_price: float
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
