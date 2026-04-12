import uuid
from datetime import datetime
from pydantic import BaseModel


class ChannelBase(BaseModel):
    channel_name: str
    department: str | None = None


class ChannelCreate(ChannelBase):
    pass


class ChannelOut(ChannelBase):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ChannelMessageCreate(BaseModel):
    channel_id: uuid.UUID
    message_content: str


class ChannelMessageOut(ChannelMessageCreate):
    id: uuid.UUID
    sender_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
