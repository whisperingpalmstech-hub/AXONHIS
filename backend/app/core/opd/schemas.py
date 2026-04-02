"""
AXONHIS Complete OPD Module — Pydantic Schemas
================================================
Request/Response schemas for all OPD orchestrator endpoints.
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal


# ═══════════════════════════════════════════════════════════════════════════════
# PRE-REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════════

class PreRegistrationCreate(BaseModel):
    first_name: str
    last_name: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    mobile_number: str
    email: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    nok_name: Optional[str] = None
    nok_relationship: Optional[str] = None
    nok_phone: Optional[str] = None
    payer_category: Optional[str] = "self_pay"
    insurance_provider: Optional[str] = None
    policy_number: Optional[str] = None
    preferred_doctor_id: Optional[UUID] = None
    preferred_department: Optional[str] = None
    preferred_date: Optional[date] = None
    photo_url: Optional[str] = None

class PreRegistrationOut(BaseModel):
    id: UUID
    pre_reg_id: str
    first_name: str
    last_name: str
    gender: Optional[str]
    date_of_birth: Optional[date]
    mobile_number: str
    email: Optional[str]
    status: str
    converted_patient_id: Optional[UUID]
    converted_uhid: Optional[str]
    duplicate_score: Optional[float]
    potential_duplicate_id: Optional[UUID]
    payer_category: Optional[str]
    preferred_department: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class ConvertPreRegRequest(BaseModel):
    """Convert pre-registration to full patient with UHID."""
    marital_status: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    allergies: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# DEPOSIT MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class DepositCreate(BaseModel):
    patient_id: UUID
    visit_id: Optional[UUID] = None
    deposit_amount: float
    payment_mode: str = "cash"
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None

class DepositOut(BaseModel):
    id: UUID
    deposit_number: str
    patient_id: UUID
    visit_id: Optional[UUID]
    deposit_amount: float
    consumed_amount: float
    balance_amount: float
    refunded_amount: float
    payment_mode: str
    transaction_reference: Optional[str]
    status: str
    collected_at: datetime
    created_at: datetime
    class Config:
        from_attributes = True

class DepositRefundRequest(BaseModel):
    reason: str
    refund_amount: Optional[float] = None  # None means full balance

class DepositConsumeRequest(BaseModel):
    bill_id: UUID
    amount: float
    notes: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# CONSENT MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class ConsentTemplateCreate(BaseModel):
    template_name: str
    template_category: str = "general"
    template_body: str
    language: str = "en"

class ConsentTemplateOut(BaseModel):
    id: UUID
    template_name: str
    template_category: str
    template_body: str
    language: str
    version: int
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class ConsentDocumentCreate(BaseModel):
    patient_id: UUID
    visit_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    consent_title: str
    consent_body: str

class ConsentDocumentSign(BaseModel):
    signature_data: str  # Base64 signature image
    signed_by_name: str
    witness_name: Optional[str] = None
    witness_designation: Optional[str] = None

class ConsentDocumentOut(BaseModel):
    id: UUID
    consent_number: str
    patient_id: UUID
    visit_id: Optional[UUID]
    template_id: Optional[UUID]
    consent_title: str
    consent_body: str
    status: str
    signature_data: Optional[str]
    signed_by_name: Optional[str]
    signed_at: Optional[datetime]
    witness_name: Optional[str]
    pdf_url: Optional[str]
    emailed_to: Optional[str]
    scanned_document_url: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class ConsentEmailRequest(BaseModel):
    email: str

class ConsentUploadRequest(BaseModel):
    document_url: str


# ═══════════════════════════════════════════════════════════════════════════════
# PRO-FORMA BILLING
# ═══════════════════════════════════════════════════════════════════════════════

class ProFormaItem(BaseModel):
    service_name: str
    quantity: int = 1
    unit_price: float

class ProFormaBillCreate(BaseModel):
    patient_id: UUID
    visit_id: Optional[UUID] = None
    items: list[ProFormaItem]
    discount_amount: float = 0.0
    notes: Optional[str] = None
    valid_days: int = 7

class ProFormaBillOut(BaseModel):
    id: UUID
    proforma_number: str
    patient_id: UUID
    items: list
    subtotal: float
    tax_amount: float
    discount_amount: float
    estimated_total: float
    valid_until: Optional[date]
    notes: Optional[str]
    converted_to_bill_id: Optional[UUID]
    generated_at: datetime
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# KIOSK CHECK-IN
# ═══════════════════════════════════════════════════════════════════════════════

class KioskCheckinRequest(BaseModel):
    kiosk_id: Optional[str] = None
    verification_method: str  # qr_code, uhid, mobile_otp
    verification_data: str  # QR value, UHID, or phone number

class KioskCheckinOut(BaseModel):
    id: UUID
    kiosk_id: Optional[str]
    verification_method: str
    patient_id: Optional[UUID]
    visit_id: Optional[UUID]
    status: str
    token_number: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# WAITLIST
# ═══════════════════════════════════════════════════════════════════════════════

class WaitlistCreate(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    department: str
    preferred_date: date
    preferred_time_start: Optional[str] = None
    preferred_time_end: Optional[str] = None
    reason: Optional[str] = None
    priority: int = 5

class WaitlistOut(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    department: str
    preferred_date: date
    status: str
    offered_slot_id: Optional[UUID]
    created_at: datetime
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# AI SCHEDULING
# ═══════════════════════════════════════════════════════════════════════════════

class AISchedulingPredictionOut(BaseModel):
    id: UUID
    booking_id: Optional[UUID]
    patient_id: UUID
    doctor_id: UUID
    appointment_date: date
    no_show_probability: float
    prediction_factors: list
    recommendation: Optional[str]
    recommendation_applied: bool
    predicted_at: datetime
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# BILL CANCELLATION
# ═══════════════════════════════════════════════════════════════════════════════

class BillCancelRequest(BaseModel):
    reason: str
    authorized_by: Optional[UUID] = None
    supporting_document_url: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYTICS DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

class OPDAnalyticsOut(BaseModel):
    analytics_date: date
    total_appointments: int
    total_walkins: int
    total_checkins: int
    total_visits: int
    completed_visits: int
    cancelled_visits: int
    no_show_count: int
    avg_wait_time_min: Optional[float]
    max_wait_time_min: Optional[float]
    avg_consultation_duration_min: Optional[float]
    doctor_utilization: dict
    total_revenue: float
    consultation_revenue: float
    diagnostic_revenue: float
    pharmacy_revenue: float
    total_deposits: float
    total_refunds: float
    department_breakdown: dict
    peak_hour: Optional[str]
    hourly_distribution: dict
    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# OPD UNIFIED PATIENT JOURNEY
# ═══════════════════════════════════════════════════════════════════════════════

class PatientJourneyStep(BaseModel):
    step_name: str
    status: str  # pending, in_progress, completed, skipped
    timestamp: Optional[datetime] = None
    details: Optional[dict] = None

class PatientJourneyOut(BaseModel):
    patient_id: UUID
    visit_id: UUID
    visit_number: str
    patient_name: str
    uhid: Optional[str]
    steps: list[PatientJourneyStep]
    current_step: str
    overall_status: str
