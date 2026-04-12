import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class PatientIdentifierBase(BaseModel):
    identifier_type: str = Field(min_length=1, max_length=50)
    identifier_value: str = Field(min_length=1, max_length=100)
    issuing_authority: str | None = None

class PatientIdentifierCreate(PatientIdentifierBase):
    pass

class PatientIdentifierOut(PatientIdentifierBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
