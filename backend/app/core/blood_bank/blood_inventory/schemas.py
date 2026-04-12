from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BloodStorageUnitBase(BaseModel):
    storage_name: str
    temperature_range: str
    capacity: int


class BloodStorageUnitCreate(BloodStorageUnitBase):
    pass


class BloodStorageUnitUpdate(BaseModel):
    storage_name: str | None = None
    temperature_range: str | None = None
    capacity: int | None = None
    current_load: int | None = None


class BloodStorageUnitResponse(BloodStorageUnitBase):
    id: UUID
    current_load: int
    created_at: datetime

    class Config:
        from_attributes = True
