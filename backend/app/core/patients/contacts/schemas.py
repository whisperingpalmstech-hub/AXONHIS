import uuid
from pydantic import BaseModel, Field

class PatientContactBase(BaseModel):
    contact_type: str = Field(min_length=1, max_length=50)
    contact_value: str = Field(min_length=1, max_length=255)
    is_primary: bool = False

class PatientContactCreate(PatientContactBase):
    pass

class PatientContactOut(PatientContactBase):
    id: uuid.UUID
    patient_id: uuid.UUID

    model_config = {"from_attributes": True}
