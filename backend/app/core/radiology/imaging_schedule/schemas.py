import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class ImagingScheduleBase(BaseModel):
    imaging_order_id: uuid.UUID
    scheduled_time: datetime
    room_id: Optional[uuid.UUID] = None
    technician_id: uuid.UUID
    status: str = "scheduled"

class ImagingScheduleCreate(ImagingScheduleBase):
    pass

class ImagingScheduleOut(ImagingScheduleBase):
    id: uuid.UUID
    scheduled_by: uuid.UUID

    class Config:
        orm_mode = True
