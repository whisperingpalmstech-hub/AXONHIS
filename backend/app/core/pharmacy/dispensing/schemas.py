import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

class DispensingRecordCreate(BaseModel):
    prescription_id: uuid.UUID
    status: str = "dispensed"

class DispensingRecordOut(DispensingRecordCreate):
    id: uuid.UUID
    dispensed_by: uuid.UUID
    dispensed_at: datetime
    model_config = ConfigDict(from_attributes=True)
