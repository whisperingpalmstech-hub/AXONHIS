import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from .models import SurgeryEventType


class SurgeryEventBase(BaseModel):
    schedule_id: uuid.UUID
    event_type: SurgeryEventType
    event_time: datetime = Field(default_factory=datetime.utcnow)
    recorded_by: uuid.UUID | None = None


class SurgeryEventCreate(SurgeryEventBase):
    pass


class SurgeryEventOut(SurgeryEventBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}
