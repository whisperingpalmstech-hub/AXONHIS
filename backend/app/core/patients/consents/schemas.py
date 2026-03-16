import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class PatientConsentBase(BaseModel):
    consent_type: str = Field(min_length=1, max_length=100)
    consent_text: str = Field(min_length=1)

class PatientConsentCreate(PatientConsentBase):
    pass

class PatientConsentOut(PatientConsentBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    signed_at: datetime
    signature_file_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}
