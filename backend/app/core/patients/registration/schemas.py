"""
Enterprise Registration Schemas.

Covers all 10 features:
  1. AI-Assisted Registration
  2. Voice-Enabled Registration
  3. ID Scan Registration (OCR)
  4. Face Recognition Check-in
  5. Duplicate Detection (AI-enhanced)
  6. Dynamic Address Auto-Population
  7. UHID Generation
  8. Health Card Generation
  9. Document Upload
  10. Notification Engine
"""
import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


# ─────────────────────────────────────────────────────────────────────────────
# 1. AI-Assisted Registration
# ─────────────────────────────────────────────────────────────────────────────

class AIRegistrationStartRequest(BaseModel):
    """Start a new AI-guided registration session."""
    language: str = Field(default="en", description="Language code: en, hi, mr")


class AIRegistrationStepRequest(BaseModel):
    """Submit answer for the current step."""
    session_id: uuid.UUID
    field_name: str = Field(description="Field being answered: name, dob, gender, mobile, email, reason_for_visit")
    field_value: str


class AIRegistrationSessionOut(BaseModel):
    id: uuid.UUID
    status: str
    current_step: int
    total_steps: int
    collected_data: dict[str, Any]
    ai_suggestions: dict[str, Any]
    next_question: str | None = None
    registration_method: str
    patient_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AIRegistrationCompleteRequest(BaseModel):
    """Complete the session and create the patient."""
    session_id: uuid.UUID


# ─────────────────────────────────────────────────────────────────────────────
# 2. Voice-Enabled Registration
# ─────────────────────────────────────────────────────────────────────────────

class VoiceRegistrationRequest(BaseModel):
    """Voice command for registration actions."""
    transcript: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en")


class VoiceRegistrationResponse(BaseModel):
    intent: str  # register_new_patient | search_by_mobile | proceed_to_billing | unknown
    confidence: float
    translated_text: str | None = None
    parsed_data: dict[str, Any] = {}
    action_taken: str | None = None
    patient_id: uuid.UUID | None = None


# ─────────────────────────────────────────────────────────────────────────────
# 3. ID Scan (OCR) Registration
# ─────────────────────────────────────────────────────────────────────────────

class IDScanRequest(BaseModel):
    """Request to extract data from a scanned ID document."""
    document_type: str = Field(description="passport | national_id | aadhaar | driving_license")
    session_id: uuid.UUID | None = None


class IDScanResultOut(BaseModel):
    id: uuid.UUID
    document_type: str
    extracted_name: str | None
    extracted_dob: str | None
    extracted_gender: str | None
    extracted_id_number: str | None
    extraction_confidence: float
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# 4. Face Recognition Check-in
# ─────────────────────────────────────────────────────────────────────────────

class FaceEnrollRequest(BaseModel):
    """Enroll a patient's face for biometric check-in."""
    patient_id: uuid.UUID


class FaceEnrollOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    quality_score: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FaceCheckInResponse(BaseModel):
    matched: bool
    patient_id: uuid.UUID | None = None
    patient_name: str | None = None
    uhid: str | None = None
    confidence: float = 0.0
    message: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# 5. AI Duplicate Detection
# ─────────────────────────────────────────────────────────────────────────────

class AIDuplicateCheckRequest(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    mobile: str | None = None
    email: EmailStr | None = None
    address: str | None = None


class DuplicateMatchOut(BaseModel):
    patient_id: uuid.UUID
    patient_uuid: str
    first_name: str
    last_name: str
    date_of_birth: str
    primary_phone: str | None
    confidence_score: float
    match_reasons: list[str] = []


class AIDuplicateCheckResponse(BaseModel):
    has_duplicates: bool
    matches: list[DuplicateMatchOut] = []
    ai_recommendation: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# 6. Address Auto-Population
# ─────────────────────────────────────────────────────────────────────────────

class AddressLookupRequest(BaseModel):
    pincode: str = Field(min_length=4, max_length=10)


class AddressLookupResponse(BaseModel):
    pincode: str
    area: str | None = None
    city: str | None = None
    state: str | None = None
    country: str = "India"
    source: str = "directory"  # directory | api


# ─────────────────────────────────────────────────────────────────────────────
# 7. UHID Generation
# ─────────────────────────────────────────────────────────────────────────────

class UHIDGenerateRequest(BaseModel):
    patient_id: uuid.UUID


class UHIDGenerateResponse(BaseModel):
    patient_id: uuid.UUID
    uhid: str
    generated_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# 8. Health Card
# ─────────────────────────────────────────────────────────────────────────────

class HealthCardGenerateRequest(BaseModel):
    patient_id: uuid.UUID


class HealthCardOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    uhid: str
    card_number: str
    qr_code_data: str  # base64 QR image
    issue_date: datetime
    is_active: bool

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# 9. Document Upload
# ─────────────────────────────────────────────────────────────────────────────

class DocumentUploadRequest(BaseModel):
    """Metadata for uploading a document (file sent as multipart)."""
    patient_id: uuid.UUID
    category: str = Field(description="id_proof | medical_document | patient_photo | insurance_card | other")
    description: str | None = None


class PatientDocumentOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    category: str
    file_name: str
    original_name: str
    file_type: str
    file_size: int
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# 10. Notification Engine
# ─────────────────────────────────────────────────────────────────────────────

class RegistrationNotifyRequest(BaseModel):
    patient_id: uuid.UUID
    channels: list[str] = Field(
        default=["sms", "email"],
        description="List of channels: sms, email, whatsapp",
    )


class RegistrationNotificationOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID | None
    channel: str
    recipient: str
    subject: str | None
    status: str
    sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RegistrationNotifyResponse(BaseModel):
    notifications_sent: int
    details: list[RegistrationNotificationOut]
