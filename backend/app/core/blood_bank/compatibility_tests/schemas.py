from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .models import CompatibilityResult


class CrossmatchTestBase(BaseModel):
    patient_id: UUID
    blood_unit_id: UUID
    patient_blood_group: str
    unit_blood_group: str


class CrossmatchTestCreate(CrossmatchTestBase):
    pass


class CrossmatchTestUpdate(BaseModel):
    compatibility_result: CompatibilityResult | None = None
    tested_by: str | None = None
    tested_at: datetime | None = None


class CrossmatchTestResponse(CrossmatchTestBase):
    id: UUID
    compatibility_result: CompatibilityResult
    tested_by: str | None
    tested_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
