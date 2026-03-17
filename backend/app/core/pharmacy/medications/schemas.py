from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from typing import Optional

class MedicationCreate(BaseModel):
    drug_code: str
    drug_name: str
    generic_name: str
    drug_class: Optional[str] = None
    form: Optional[str] = None
    strength: Optional[str] = None
    manufacturer: Optional[str] = None

class MedicationOut(MedicationCreate):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
