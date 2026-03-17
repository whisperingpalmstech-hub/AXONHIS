from pydantic import BaseModel, ConfigDict
import uuid
from datetime import date
from typing import Optional

class DrugBatchCreate(BaseModel):
    drug_id: uuid.UUID
    batch_number: str
    manufacture_date: date
    expiry_date: date
    quantity: float

class DrugBatchOut(DrugBatchCreate):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)
