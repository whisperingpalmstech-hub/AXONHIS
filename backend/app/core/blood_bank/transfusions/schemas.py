from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .models import TransfusionStatus


class TransfusionBase(BaseModel):
    patient_id: UUID
    encounter_id: UUID | None = None
    blood_unit_id: UUID
    administered_by: str
    supervised_by: str | None = None


class TransfusionCreate(TransfusionBase):
    pass


class TransfusionUpdate(BaseModel):
    transfusion_end_time: datetime | None = None
    transfusion_status: TransfusionStatus | None = None


class TransfusionResponse(TransfusionBase):
    id: UUID
    transfusion_start_time: datetime
    transfusion_end_time: datetime | None
    transfusion_status: TransfusionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
