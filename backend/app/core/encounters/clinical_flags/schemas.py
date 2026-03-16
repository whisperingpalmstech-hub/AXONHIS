import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class ClinicalFlagBase(BaseModel):
    flag_type: str = Field(min_length=1, max_length=100)
    flag_description: str = Field(min_length=1, max_length=500)

class ClinicalFlagCreate(ClinicalFlagBase):
    pass

class ClinicalFlagOut(ClinicalFlagBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
