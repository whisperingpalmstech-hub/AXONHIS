import uuid
from datetime import date
from pydantic import BaseModel, Field

class PatientInsuranceBase(BaseModel):
    insurance_provider: str = Field(min_length=1, max_length=150)
    policy_number: str | None = Field(default=None, max_length=100)
    coverage_type: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None

class PatientInsuranceCreate(PatientInsuranceBase):
    pass

class PatientInsuranceOut(PatientInsuranceBase):
    id: uuid.UUID
    patient_id: uuid.UUID

    model_config = {"from_attributes": True}
