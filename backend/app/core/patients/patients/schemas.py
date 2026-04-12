from datetime import date, datetime
import uuid
from pydantic import BaseModel, Field, EmailStr

# We use string references for forward/circular dependencies where needed,
# or import them if strictly layered.

class PatientBase(BaseModel):
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    date_of_birth: date
    gender: str = Field(max_length=20)
    primary_phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    blood_group: str | None = None
    allergies: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    primary_phone: str | None = None
    email: EmailStr | None = None
    status: str | None = None
    address: str | None = None
    blood_group: str | None = None
    allergies: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None

from typing import List
from app.core.patients.identifiers.schemas import PatientIdentifierOut
from app.core.patients.contacts.schemas import PatientContactOut
from app.core.patients.guardians.schemas import PatientGuardianOut
from app.core.patients.insurance.schemas import PatientInsuranceOut
from app.core.patients.consents.schemas import PatientConsentOut
from app.core.patients.appointments.schemas import AppointmentOut

class PatientOut(PatientBase):
    id: uuid.UUID
    patient_uuid: str
    mrn: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    # Full details to be populated dynamically
    identifiers: List[PatientIdentifierOut] = []
    contacts: List[PatientContactOut] = []
    guardians: List[PatientGuardianOut] = []
    insurance: List[PatientInsuranceOut] = []
    consents: List[PatientConsentOut] = []
    appointments: List[AppointmentOut] = []

    model_config = {"from_attributes": True}
