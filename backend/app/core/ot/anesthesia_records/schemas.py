import uuid
from datetime import datetime
from pydantic import BaseModel
from .models import AnesthesiaType


class AnesthesiaRecordBase(BaseModel):
    schedule_id: uuid.UUID
    anesthesia_type: AnesthesiaType
    anesthesia_start_time: datetime | None = None
    anesthesia_end_time: datetime | None = None
    anesthesiologist_id: uuid.UUID | None = None
    notes: str | None = None


class AnesthesiaRecordCreate(AnesthesiaRecordBase):
    pass


class AnesthesiaRecordUpdate(BaseModel):
    anesthesia_type: AnesthesiaType | None = None
    anesthesia_start_time: datetime | None = None
    anesthesia_end_time: datetime | None = None
    anesthesiologist_id: uuid.UUID | None = None
    notes: str | None = None


class AnesthesiaRecordOut(AnesthesiaRecordBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}
