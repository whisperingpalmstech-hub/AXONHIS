import uuid
from datetime import datetime
from pydantic import BaseModel


class PatientThreadBase(BaseModel):
    patient_id: uuid.UUID


class PatientThreadCreate(PatientThreadBase):
    pass


class PatientThreadOut(PatientThreadBase):
    id: uuid.UUID
    created_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
