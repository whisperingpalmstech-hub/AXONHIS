import uuid
from datetime import datetime
from pydantic import BaseModel
from .models import MessageType, MessageStatus


class MessageBase(BaseModel):
    receiver_id: uuid.UUID
    message_content: str
    message_type: MessageType = MessageType.TEXT


class MessageCreate(MessageBase):
    pass


class MessageOut(MessageBase):
    id: uuid.UUID
    sender_id: uuid.UUID
    status: MessageStatus
    created_at: datetime

    model_config = {"from_attributes": True}
