import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from .models import SurgeryPriority, SurgeryStatus


class SurgeryScheduleBase(BaseModel):
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
    procedure_id: uuid.UUID
    operating_room_id: uuid.UUID
    scheduled_start_time: datetime
    scheduled_end_time: datetime
    priority: SurgeryPriority = SurgeryPriority.ELECTIVE
    status: SurgeryStatus = SurgeryStatus.SCHEDULED


class SurgeryScheduleCreate(SurgeryScheduleBase):
    scheduled_by: uuid.UUID | None = None


class SurgeryScheduleUpdate(BaseModel):
    operating_room_id: uuid.UUID | None = None
    scheduled_start_time: datetime | None = None
    scheduled_end_time: datetime | None = None
    priority: SurgeryPriority | None = None
    status: SurgeryStatus | None = None


class SurgeryScheduleOut(SurgeryScheduleBase):
    id: uuid.UUID
    scheduled_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
