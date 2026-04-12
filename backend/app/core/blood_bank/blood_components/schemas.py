from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BloodComponentBase(BaseModel):
    component_name: str
    storage_temperature: str
    shelf_life_days: int


class BloodComponentCreate(BloodComponentBase):
    pass


class BloodComponentUpdate(BaseModel):
    component_name: str | None = None
    storage_temperature: str | None = None
    shelf_life_days: int | None = None


class BloodComponentResponse(BloodComponentBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
