from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from .models import ScreeningStatus


# --- Blood Donor Schemas ---
class BloodDonorBase(BaseModel):
    donor_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    blood_group: str
    rh_factor: str
    contact_number: str
    screening_status: ScreeningStatus = ScreeningStatus.ELIGIBLE


class BloodDonorCreate(BloodDonorBase):
    pass


class BloodDonorUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    contact_number: str | None = None
    screening_status: ScreeningStatus | None = None
    last_donation_date: date | None = None


class BloodDonorResponse(BloodDonorBase):
    id: UUID
    last_donation_date: date | None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Blood Collection Schemas ---
class BloodCollectionBase(BaseModel):
    donor_id: UUID
    collection_date: datetime
    collection_location: str
    collected_by: str
    collection_volume: float
    screening_results: dict = {}


class BloodCollectionCreate(BloodCollectionBase):
    pass


class BloodCollectionUpdate(BaseModel):
    screening_results: dict | None = None


class BloodCollectionResponse(BloodCollectionBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
