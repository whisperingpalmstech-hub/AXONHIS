from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .models import BloodUnitStatus


class BloodUnitBase(BaseModel):
    unit_id: str
    blood_group: str
    rh_factor: str
    component_type: UUID | None = None
    collection_id: UUID
    collection_date: datetime
    expiry_date: datetime
    storage_location: UUID | None = None
    status: BloodUnitStatus = BloodUnitStatus.AVAILABLE


class BloodUnitCreate(BloodUnitBase):
    pass


class BloodUnitUpdate(BaseModel):
    storage_location: UUID | None = None
    status: BloodUnitStatus | None = None


class BloodUnitResponse(BloodUnitBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
