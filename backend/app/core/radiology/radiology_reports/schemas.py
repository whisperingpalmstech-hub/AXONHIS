import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class RadiologyReportBase(BaseModel):
    study_id: uuid.UUID
    report_text: str
    status: str = "draft"

class RadiologyReportCreate(RadiologyReportBase):
    pass

class RadiologyReportOut(RadiologyReportBase):
    id: uuid.UUID
    reported_by: uuid.UUID
    reported_at: datetime

    class Config:
        orm_mode = True
