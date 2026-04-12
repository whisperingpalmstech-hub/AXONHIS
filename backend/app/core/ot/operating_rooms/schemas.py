import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from .models import OperatingRoomStatus


class OperatingRoomBase(BaseModel):
    room_code: str = Field(..., min_length=1, max_length=50)
    room_name: str = Field(..., min_length=1, max_length=100)
    department: str = Field(..., min_length=1, max_length=100)
    equipment_profile: dict | None = None
    status: OperatingRoomStatus = OperatingRoomStatus.AVAILABLE


class OperatingRoomCreate(OperatingRoomBase):
    pass


class OperatingRoomUpdate(BaseModel):
    room_name: str | None = None
    department: str | None = None
    equipment_profile: dict | None = None
    status: OperatingRoomStatus | None = None


class OperatingRoomOut(OperatingRoomBase):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
