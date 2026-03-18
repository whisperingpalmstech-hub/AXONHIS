from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional
from datetime import datetime

class DrugClassBase(BaseModel):
    drug_id: str
    drug_class: str
    therapeutic_group: str

class DrugClassCreate(DrugClassBase):
    pass

class DrugClassResponse(DrugClassBase):
    id: UUID4
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)