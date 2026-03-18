import uuid
from datetime import datetime
from pydantic import BaseModel


class SurgicalTeamBase(BaseModel):
    schedule_id: uuid.UUID
    lead_surgeon_id: uuid.UUID | None = None
    assistant_surgeon_id: uuid.UUID | None = None
    anesthesiologist_id: uuid.UUID | None = None
    scrub_nurse_id: uuid.UUID | None = None
    circulating_nurse_id: uuid.UUID | None = None


class SurgicalTeamCreate(SurgicalTeamBase):
    pass


class SurgicalTeamUpdate(BaseModel):
    lead_surgeon_id: uuid.UUID | None = None
    assistant_surgeon_id: uuid.UUID | None = None
    anesthesiologist_id: uuid.UUID | None = None
    scrub_nurse_id: uuid.UUID | None = None
    circulating_nurse_id: uuid.UUID | None = None


class SurgicalTeamOut(SurgicalTeamBase):
    id: uuid.UUID
    assigned_at: datetime

    model_config = {"from_attributes": True}
