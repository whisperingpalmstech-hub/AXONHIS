import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class PostoperativeEventBase(BaseModel):
    schedule_id: uuid.UUID
    event_type: str
    event_time: datetime = Field(default_factory=datetime.utcnow)
    recorded_by: uuid.UUID | None = None


class PostoperativeEventCreate(PostoperativeEventBase):
    pass


class PostoperativeEventOut(PostoperativeEventBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}
