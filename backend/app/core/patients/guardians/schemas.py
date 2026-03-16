import uuid
from pydantic import BaseModel, Field

class PatientGuardianBase(BaseModel):
    guardian_name: str = Field(min_length=1, max_length=150)
    relationship_type: str = Field(alias="relationship", min_length=1, max_length=50)
    phone_number: str | None = None
    address: str | None = None

class PatientGuardianCreate(PatientGuardianBase):
    pass

class PatientGuardianOut(PatientGuardianBase):
    id: uuid.UUID
    patient_id: uuid.UUID

    model_config = {"from_attributes": True, "populate_by_name": True}
