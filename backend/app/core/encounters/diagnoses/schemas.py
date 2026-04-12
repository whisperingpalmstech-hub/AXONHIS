import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class EncounterDiagnosisBase(BaseModel):
    diagnosis_code: str = Field(min_length=1, max_length=50)
    diagnosis_description: str = Field(min_length=1, max_length=255)
    diagnosis_type: str = Field(min_length=1, max_length=50)

class EncounterDiagnosisCreate(EncounterDiagnosisBase):
    pass

class EncounterDiagnosisOut(EncounterDiagnosisBase):
    id: uuid.UUID
    encounter_id: uuid.UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}
