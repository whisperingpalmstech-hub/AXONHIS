import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

class EncounterTimelineBase(BaseModel):
    event_type: str = Field(min_length=1, max_length=100)
    description: str | None = None
    metadata_json: dict[str, Any] | None = None

class EncounterTimelineCreate(EncounterTimelineBase):
    pass

class EncounterTimelineOut(EncounterTimelineBase):
    id: uuid.UUID
    encounter_id: uuid.UUID
    event_time: datetime
    actor_id: uuid.UUID

    model_config = {"from_attributes": True}
