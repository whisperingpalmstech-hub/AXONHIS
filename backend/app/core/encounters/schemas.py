"""Encounter schemas."""
import uuid
from datetime import datetime

from pydantic import BaseModel


class EncounterCreate(BaseModel):
    patient_id: uuid.UUID
    encounter_type: str
    chief_complaint: str | None = None
    ward: str | None = None
    room: str | None = None
    bed: str | None = None
    notes: str | None = None


class EncounterOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    encounter_type: str
    status: str
    doctor_id: uuid.UUID | None
    chief_complaint: str | None
    ward: str | None
    room: str | None
    bed: str | None
    admitted_at: datetime
    discharged_at: datetime | None

    model_config = {"from_attributes": True}


class EncounterDischarge(BaseModel):
    notes: str | None = None
