import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from .models import PatientAccountStatus

class PatientAccountBase(BaseModel):
    email: EmailStr
    phone_number: str | None = None

class PatientAccountCreate(PatientAccountBase):
    patient_id: uuid.UUID
    password: str

class PatientAccountLogin(BaseModel):
    email: str
    password: str

class PatientAccountOTP(BaseModel):
    email: str
    otp: str

class PatientAccountOut(PatientAccountBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    account_status: str
    first_name: str | None = None
    last_name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
