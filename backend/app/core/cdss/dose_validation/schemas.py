from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional
from datetime import datetime

class DrugDosageGuidelineBase(BaseModel):
    drug_id: str
    min_dose: float
    max_dose: float
    age_group: Optional[str] = None
    weight_range: Optional[str] = None

class DrugDosageGuidelineCreate(DrugDosageGuidelineBase):
    pass

class DrugDosageGuidelineResponse(DrugDosageGuidelineBase):
    id: UUID4
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)