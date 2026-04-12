import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class RadiologyResultBase(BaseModel):
    study_id: uuid.UUID
    impression: str
    critical_flag: bool = False

class RadiologyResultCreate(RadiologyResultBase):
    pass

class RadiologyResultOut(RadiologyResultBase):
    id: uuid.UUID
    published_at: datetime

    class Config:
        orm_mode = True
