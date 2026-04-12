from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional
from datetime import datetime

class DrugContraindicationBase(BaseModel):
    drug_id: str
    contraindicated_condition: str
    risk_description: str

class DrugContraindicationCreate(DrugContraindicationBase):
    pass

class DrugContraindicationResponse(DrugContraindicationBase):
    id: UUID4
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)