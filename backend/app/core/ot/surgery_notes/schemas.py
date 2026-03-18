import uuid
from datetime import datetime
from pydantic import BaseModel
from .models import SurgeryNoteType


class SurgeryNoteBase(BaseModel):
    schedule_id: uuid.UUID
    note_type: SurgeryNoteType
    content: str
    created_by: uuid.UUID | None = None


class SurgeryNoteCreate(SurgeryNoteBase):
    pass


class SurgeryNoteUpdate(BaseModel):
    note_type: SurgeryNoteType | None = None
    content: str | None = None


class SurgeryNoteOut(SurgeryNoteBase):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
