"""Patient schemas – request and response Pydantic models."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class PatientCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    gender: str
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    blood_group: str = "UNKNOWN"
    allergies: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    blood_group: str | None = None
    allergies: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class PatientOut(BaseModel):
    id: uuid.UUID
    mrn: str
    first_name: str
    last_name: str
    full_name: str
    date_of_birth: date
    gender: str
    phone: str | None
    email: str | None
    blood_group: str
    allergies: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PatientListOut(BaseModel):
    total: int
    items: list[PatientOut]
