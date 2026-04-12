import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class AppointmentBase(BaseModel):
    doctor_id: uuid.UUID | None = None
    department: str = Field(min_length=1, max_length=100)
    appointment_time: datetime
    status: str = Field(default="scheduled", min_length=1, max_length=50)

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    doctor_id: uuid.UUID | None = None
    department: str | None = None
    appointment_time: datetime | None = None
    status: str | None = None

class AppointmentOut(AppointmentBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
