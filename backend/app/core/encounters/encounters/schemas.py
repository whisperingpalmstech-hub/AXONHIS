import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.encounters.diagnoses.schemas import EncounterDiagnosisOut
from app.core.encounters.notes.schemas import EncounterNoteOut
from app.core.encounters.timeline.schemas import EncounterTimelineOut

class EncounterBase(BaseModel):
    patient_id: uuid.UUID
    encounter_type: str = Field(min_length=1, max_length=50) # OP, IP, ER, FOLLOW_UP
    doctor_id: Optional[uuid.UUID] = None
    department: str = Field(min_length=1, max_length=100)
    status: str = "scheduled"

class EncounterCreate(EncounterBase):
    pass

class EncounterUpdate(BaseModel):
    status: str | None = None
    department: str | None = None

class EncounterOut(EncounterBase):
    id: uuid.UUID
    encounter_uuid: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    diagnoses: List[EncounterDiagnosisOut] = []
    notes: List[EncounterNoteOut] = []
    timeline_events: List[EncounterTimelineOut] = []

    model_config = {"from_attributes": True}
