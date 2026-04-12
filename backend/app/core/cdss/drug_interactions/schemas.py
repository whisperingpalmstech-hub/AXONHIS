from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional, List
from datetime import datetime

class DrugInteractionBase(BaseModel):
    drug_a: str
    drug_b: str
    severity: str
    interaction_description: str

class DrugInteractionCreate(DrugInteractionBase):
    pass

class DrugInteractionResponse(DrugInteractionBase):
    id: UUID4
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)