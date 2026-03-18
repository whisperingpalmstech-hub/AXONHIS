import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class ImagingStudyBase(BaseModel):
    imaging_order_id: uuid.UUID
    study_uid: str
    modality: str
    machine_id: Optional[str] = None
    status: str = "scheduled"

class ImagingStudyCreate(ImagingStudyBase):
    pass

class ImagingStudyOut(ImagingStudyBase):
    id: uuid.UUID
    study_start_time: Optional[datetime] = None
    study_end_time: Optional[datetime] = None

    class Config:
        orm_mode = True
