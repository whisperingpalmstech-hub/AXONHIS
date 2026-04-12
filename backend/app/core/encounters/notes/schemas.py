import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class EncounterNoteBase(BaseModel):
    note_type: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)

class EncounterNoteCreate(EncounterNoteBase):
    pass

class EncounterNoteOut(EncounterNoteBase):
    id: uuid.UUID
    encounter_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
