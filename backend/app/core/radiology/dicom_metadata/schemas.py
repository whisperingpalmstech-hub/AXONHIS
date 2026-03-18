import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class DICOMMetadataBase(BaseModel):
    study_uid: str
    series_uid: str
    image_count: int = 1
    file_location: Optional[str] = None

class DICOMMetadataCreate(DICOMMetadataBase):
    pass

class DICOMMetadataOut(DICOMMetadataBase):
    id: uuid.UUID
    uploaded_at: datetime

    class Config:
        orm_mode = True
