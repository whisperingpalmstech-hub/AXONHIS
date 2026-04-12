"""
AXONHIS Complete OPD Module — Enhanced Database Models
======================================================
New entities layered on top of existing OPD infrastructure:
  - PreRegistration         : Temporary patient record before UHID assignment
  - OPDDeposit              : Advance deposit management
  - OPDDepositConsumption   : Tracks deposit usage against bills
  - OPDConsentDocument      : Consent forms with digital signatures
  - OPDConsentTemplate      : Reusable consent form templates
  - OPDProFormaBill         : Cost estimate bills (non-financial)
  - OPDKioskCheckin         : Self-check-in kiosk sessions
  - OPDPatientNotification  : OPD-specific notifications (queue, billing, appointment)
  - OPDDailyAnalytics       : Pre-computed daily OPD metrics
  - OPDWaitlistEntry        : Appointment waitlist management
  - AISchedulingPrediction  : AI no-show prediction and calendar optimization
"""
import uuid
from datetime import datetime, date, timezone
from enum import StrEnum
from sqlalchemy import (
    Column, String, Text, DateTime, Date, Boolean, Integer, Float,
    Numeric, ForeignKey, Index, JSON, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


# ── Enums ────────────────────────────────────────────────────────────────────

class PreRegStatus(StrEnum):
    PENDING = "pending"
    CONVERTED = "converted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class DepositStatus(StrEnum):
    ACTIVE = "active"
    PARTIALLY_CONSUMED = "partially_consumed"
    FULLY_CONSUMED = "fully_consumed"
    REFUNDED = "refunded"

class ConsentStatus(StrEnum):
    DRAFT = "draft"
    PENDING_SIGNATURE = "pending_signature"
    SIGNED = "signed"
    REVOKED = "revoked"

class KioskStatus(StrEnum):
    STARTED = "started"
    IDENTITY_VERIFIED = "identity_verified"
    CHECKED_IN = "checked_in"
    FAILED = "failed"

class NotificationType(StrEnum):
    APPOINTMENT_REMINDER = "appointment_reminder"
    QUEUE_UPDATE = "queue_update"
    BILLING_UPDATE = "billing_update"
    PRESCRIPTION_READY = "prescription_ready"
    LAB_RESULT_READY = "lab_result_ready"
    VISIT_SUMMARY = "visit_summary"


# ── 1. Pre-Registration ─────────────────────────────────────────────────────

class PreRegistration(Base):
    """Temporary patient record before full UHID registration."""
    __tablename__ = "opd_pre_registrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pre_reg_id = Column(String(30), unique=True, nullable=False, index=True)  # PRE-YYYYMMDD-XXXXXX
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Basic demographics (minimal for pre-reg)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    gender = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    mobile_number = Column(String(20), nullable=False)
    email = Column(String(150), nullable=True)
    
    # Address
    address_line = Column(String(300), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)

    # Next-of-kin
    nok_name = Column(String(100), nullable=True)
    nok_relationship = Column(String(50), nullable=True)
    nok_phone = Column(String(20), nullable=True)

    # Payer
    payer_category = Column(String(50), nullable=True)  # self_pay, insurance, corporate
    insurance_provider = Column(String(200), nullable=True)
    policy_number = Column(String(100), nullable=True)

    # Appointment link
    appointment_id = Column(UUID(as_uuid=True), nullable=True)
    preferred_doctor_id = Column(UUID(as_uuid=True), nullable=True)
    preferred_department = Column(String(100), nullable=True)
    preferred_date = Column(Date, nullable=True)

    # Status
    status = Column(String(30), default=PreRegStatus.PENDING, nullable=False)
    converted_patient_id = Column(UUID(as_uuid=True), nullable=True)  # Patient.id after UHID generation
    converted_uhid = Column(String(50), nullable=True)

    # Duplicate detection
    duplicate_score = Column(Float, nullable=True)  # Fuzzy match score (0-1)
    potential_duplicate_id = Column(UUID(as_uuid=True), nullable=True)  # Matched existing patient

    # Photo
    photo_url = Column(String(500), nullable=True)

    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_prereg_mobile", "mobile_number"),
        Index("ix_prereg_status", "status"),
    )


# ── 2. OPD Deposit Management ───────────────────────────────────────────────

class OPDDeposit(Base):
    """Advance deposit made by a patient for OPD services."""
    __tablename__ = "opd_deposits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deposit_number = Column(String(30), unique=True, nullable=False, index=True)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), nullable=True)

    deposit_amount = Column(Numeric(12, 2), nullable=False)
    consumed_amount = Column(Numeric(12, 2), default=0.00)
    balance_amount = Column(Numeric(12, 2), nullable=False)
    refunded_amount = Column(Numeric(12, 2), default=0.00)

    payment_mode = Column(String(50), nullable=False)  # cash, card, upi, bank_transfer
    transaction_reference = Column(String(200), nullable=True)
    receipt_number = Column(String(50), nullable=True)

    status = Column(String(30), default=DepositStatus.ACTIVE, nullable=False)
    
    collected_by = Column(UUID(as_uuid=True), nullable=False)
    collected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    refund_reason = Column(Text, nullable=True)
    refunded_by = Column(UUID(as_uuid=True), nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_deposit_patient", "patient_id"),
    )


class OPDDepositConsumption(Base):
    """Tracks individual consumption of deposit against billing items."""
    __tablename__ = "opd_deposit_consumptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deposit_id = Column(UUID(as_uuid=True), ForeignKey("opd_deposits.id"), nullable=False)
    bill_id = Column(UUID(as_uuid=True), nullable=False)  # rcm_billing_master.id
    
    consumed_amount = Column(Numeric(12, 2), nullable=False)
    consumed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    consumed_by = Column(UUID(as_uuid=True), nullable=False)
    notes = Column(Text, nullable=True)


# ── 3. Consent Document Management ──────────────────────────────────────────

class OPDConsentTemplate(Base):
    """Reusable consent form templates."""
    __tablename__ = "opd_consent_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    template_name = Column(String(200), nullable=False)
    template_category = Column(String(100), nullable=False)  # general, surgical, anesthesia, research
    template_body = Column(Text, nullable=False)  # HTML/Rich text template
    
    language = Column(String(10), default="en")
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class OPDConsentDocument(Base):
    """Patient-specific consent document with digital signature."""
    __tablename__ = "opd_consent_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    consent_number = Column(String(30), unique=True, nullable=False, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), nullable=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("opd_consent_templates.id"), nullable=True)

    consent_title = Column(String(200), nullable=False)
    consent_body = Column(Text, nullable=False)  # Actual consent content (may be edited from template)
    
    status = Column(String(30), default=ConsentStatus.DRAFT, nullable=False)
    
    # Digital signature
    signature_data = Column(Text, nullable=True)  # Base64 image of signature
    signed_by_name = Column(String(200), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    witness_name = Column(String(200), nullable=True)
    witness_designation = Column(String(100), nullable=True)
    
    # Document storage
    pdf_url = Column(String(500), nullable=True)
    emailed_to = Column(String(200), nullable=True)
    emailed_at = Column(DateTime(timezone=True), nullable=True)
    printed_at = Column(DateTime(timezone=True), nullable=True)

    # Scanned document upload
    scanned_document_url = Column(String(500), nullable=True)

    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


# ── 4. Pro-Forma Billing ────────────────────────────────────────────────────

class OPDProFormaBill(Base):
    """Cost estimate bill — does not affect financial accounts."""
    __tablename__ = "opd_proforma_bills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    proforma_number = Column(String(30), unique=True, nullable=False, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False)
    visit_id = Column(UUID(as_uuid=True), nullable=True)

    items = Column(JSON, default=list)  # [{service_name, quantity, unit_price, total}]
    
    subtotal = Column(Numeric(12, 2), default=0.00)
    tax_amount = Column(Numeric(12, 2), default=0.00)
    discount_amount = Column(Numeric(12, 2), default=0.00)
    estimated_total = Column(Numeric(12, 2), default=0.00)

    valid_until = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    
    converted_to_bill_id = Column(UUID(as_uuid=True), nullable=True)
    
    generated_by = Column(UUID(as_uuid=True), nullable=False)
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ── 5. Self Check-in Kiosk ──────────────────────────────────────────────────

class OPDKioskCheckin(Base):
    """Tracks self-check-in kiosk sessions."""
    __tablename__ = "opd_kiosk_checkins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    kiosk_id = Column(String(50), nullable=True)  # Physical kiosk identifier
    
    # Verification method
    verification_method = Column(String(30), nullable=False)  # qr_code, uhid, mobile_otp, face_recognition
    verification_data = Column(String(200), nullable=True)  # QR value / UHID / phone
    
    patient_id = Column(UUID(as_uuid=True), nullable=True)
    appointment_id = Column(UUID(as_uuid=True), nullable=True)
    visit_id = Column(UUID(as_uuid=True), nullable=True)  # Generated visit after check-in
    
    status = Column(String(30), default=KioskStatus.STARTED, nullable=False)
    token_number = Column(String(20), nullable=True)
    
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)


# ── 6. OPD Notifications ────────────────────────────────────────────────────

class OPDPatientNotification(Base):
    """OPD-specific patient notifications."""
    __tablename__ = "opd_patient_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    visit_id = Column(UUID(as_uuid=True), nullable=True)
    
    notification_type = Column(String(50), nullable=False)
    channel = Column(String(30), nullable=False)  # sms, email, whatsapp, push
    recipient = Column(String(200), nullable=False)
    
    title = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)
    extra_data = Column(JSON, default=dict)  # Additional data (queue_position, wait_time, etc.)
    
    status = Column(String(30), default="sent")
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ── 7. Appointment Waitlist ─────────────────────────────────────────────────

class OPDWaitlistEntry(Base):
    """Waitlist for fully-booked appointment slots."""
    __tablename__ = "opd_waitlist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), nullable=False)
    department = Column(String(100), nullable=False)
    
    preferred_date = Column(Date, nullable=False)
    preferred_time_start = Column(String(10), nullable=True)
    preferred_time_end = Column(String(10), nullable=True)
    
    reason = Column(Text, nullable=True)
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest
    
    status = Column(String(30), default="waiting")  # waiting, offered, confirmed, expired
    offered_slot_id = Column(UUID(as_uuid=True), nullable=True)
    notified_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)


# ── 8. AI Scheduling Predictions ────────────────────────────────────────────

class AISchedulingPrediction(Base):
    """AI predictions for no-show probability and optimal scheduling."""
    __tablename__ = "opd_ai_scheduling_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    booking_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # slot_bookings.id
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), nullable=False)
    
    appointment_date = Column(Date, nullable=False)
    
    # No-show prediction
    no_show_probability = Column(Float, default=0.0)
    prediction_factors = Column(JSON, default=list)  # ["prev_no_shows": 2, "distance_km": 45]
    
    # Recommendation
    recommendation = Column(String(50), nullable=True)  # overbook, send_reminder, call_confirm
    recommendation_applied = Column(Boolean, default=False)
    
    predicted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ── 9. OPD Daily Analytics ──────────────────────────────────────────────────

class OPDDailyAnalytics(Base):
    """Pre-computed daily OPD analytics across all metrics."""
    __tablename__ = "opd_daily_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    analytics_date = Column(Date, nullable=False, index=True)

    # Volume
    total_appointments = Column(Integer, default=0)
    total_walkins = Column(Integer, default=0)
    total_checkins = Column(Integer, default=0)
    total_visits = Column(Integer, default=0)
    completed_visits = Column(Integer, default=0)
    cancelled_visits = Column(Integer, default=0)
    no_show_count = Column(Integer, default=0)

    # Wait times
    avg_wait_time_min = Column(Float, nullable=True)
    max_wait_time_min = Column(Float, nullable=True)
    median_wait_time_min = Column(Float, nullable=True)

    # Consultation
    avg_consultation_duration_min = Column(Float, nullable=True)
    
    # Doctor utilization
    doctor_utilization = Column(JSON, default=dict)  # {doctor_id: {slots, utilized, pct}}
    
    # Revenue
    total_revenue = Column(Numeric(14, 2), default=0.00)
    consultation_revenue = Column(Numeric(14, 2), default=0.00)
    diagnostic_revenue = Column(Numeric(14, 2), default=0.00)
    pharmacy_revenue = Column(Numeric(14, 2), default=0.00)
    total_deposits = Column(Numeric(14, 2), default=0.00)
    total_refunds = Column(Numeric(14, 2), default=0.00)

    # Department breakdown
    department_breakdown = Column(JSON, default=dict)  # {dept: {visits, revenue}}
    
    # Patient flow
    peak_hour = Column(String(10), nullable=True)
    hourly_distribution = Column(JSON, default=dict)  # {"08": 12, "09": 25, ...}

    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("analytics_date", "org_id", name="uq_opd_analytics_date_org"),
    )


# ── 10. Bill Cancellation Audit ─────────────────────────────────────────────

class OPDBillCancellationLog(Base):
    """Audit log for bill cancellations with mandatory reason."""
    __tablename__ = "opd_bill_cancellation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    bill_id = Column(UUID(as_uuid=True), nullable=False)
    bill_number = Column(String(50), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    
    original_amount = Column(Numeric(12, 2), nullable=False)
    cancellation_reason = Column(Text, nullable=False)
    
    cancelled_by = Column(UUID(as_uuid=True), nullable=False)
    authorized_by = Column(UUID(as_uuid=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    supporting_document_url = Column(String(500), nullable=True)
