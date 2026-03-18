from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional
from datetime import datetime

class DrugAllergyMappingBase(BaseModel):
    allergy_type: str
    drug_class: str
    reaction_risk: str

class DrugAllergyMappingCreate(DrugAllergyMappingBase):
    pass

class DrugAllergyMappingResponse(DrugAllergyMappingBase):
    id: UUID4
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)