import uuid
from datetime import datetime
from pydantic import BaseModel
from .models import NotificationStatus


class NotificationBase(BaseModel):
    user_id: uuid.UUID
    notification_type: str
    reference_id: uuid.UUID | None = None
    message: str


class NotificationCreate(NotificationBase):
    pass


class NotificationOut(NotificationBase):
    id: uuid.UUID
    status: NotificationStatus
    created_at: datetime

    model_config = {"from_attributes": True}
