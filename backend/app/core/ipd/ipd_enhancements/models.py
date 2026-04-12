"""
IPD FRD Gap: Admission Estimation, Pre-Auth, Discharge Summary, Diet Management
==================================================================================
Fills the IPD FRD gaps identified in the gap analysis.
Interconnected with:
- billing_masters → PricingEngine for cost estimation
- er → for ER-to-IPD admission transfer
- pharmacy → for medication reconciliation at discharge
- wards → for bed management
"""
import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class IPDAdmissionEstimate(Base):
    """Pre-admission cost estimation — links to billing_masters.BillEstimation."""
    __tablename__ = "ipd_admission_estimates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    admission_request_id = Column(UUID(as_uuid=True), nullable=True)
    patient_id = Column(UUID(as_uuid=True), nullable=True)
    patient_name = Column(String(255), nullable=False)
    bed_category = Column(String(100), nullable=True)
    expected_stay_days = Column(Integer, default=3)
    package_id = Column(UUID(as_uuid=True), nullable=True)
    estimated_room_charges = Column(Numeric(12, 2), default=0)
    estimated_procedure_charges = Column(Numeric(12, 2), default=0)
    estimated_pharmacy_charges = Column(Numeric(12, 2), default=0)
    estimated_lab_charges = Column(Numeric(12, 2), default=0)
    estimated_misc_charges = Column(Numeric(12, 2), default=0)
    total_estimated_cost = Column(Numeric(14, 2), default=0)
    deposit_required = Column(Numeric(12, 2), default=0)
    insurance_coverage = Column(Numeric(12, 2), default=0)
    patient_liability = Column(Numeric(12, 2), default=0)
    estimation_details = Column(JSONB, nullable=True)
    status = Column(String(30), default="draft")  # draft, shared, confirmed
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class IPDPreAuthorization(Base):
    """Insurance pre-authorization tracking for IPD admissions."""
    __tablename__ = "ipd_pre_authorizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    admission_id = Column(UUID(as_uuid=True), nullable=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    insurance_detail_id = Column(UUID(as_uuid=True), nullable=True)
    pre_auth_number = Column(String(100), nullable=True)
    requested_amount = Column(Numeric(14, 2), nullable=False)
    approved_amount = Column(Numeric(14, 2), nullable=True)
    status = Column(String(30), default="pending")  # pending, approved, rejected, enhanced, closed
    diagnosis_codes = Column(JSONB, nullable=True)
    procedure_codes = Column(JSONB, nullable=True)
    expected_stay_days = Column(Integer, nullable=True)
    bed_category = Column(String(100), nullable=True)
    remarks = Column(Text, nullable=True)
    response_notes = Column(Text, nullable=True)
    requested_by = Column(UUID(as_uuid=True), nullable=False)
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    responded_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class IPDDischargeSummaryEnhanced(Base):
    """Enhanced discharge summary — auto-populated from encounter data."""
    __tablename__ = "ipd_discharge_summaries_v2"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    admission_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    summary_number = Column(String(50), unique=True, nullable=False)

    # Clinical summary
    admission_diagnosis = Column(Text, nullable=True)
    discharge_diagnosis = Column(Text, nullable=True)
    clinical_summary = Column(Text, nullable=True)
    hospital_course = Column(Text, nullable=True)
    procedures_performed = Column(JSONB, nullable=True)
    investigation_results = Column(JSONB, nullable=True)
    condition_at_discharge = Column(String(100), nullable=True)  # improved, unchanged, deteriorated, expired

    # Discharge instructions
    discharge_medications = Column(JSONB, nullable=True)
    diet_instructions = Column(Text, nullable=True)
    activity_restrictions = Column(Text, nullable=True)
    wound_care = Column(Text, nullable=True)
    follow_up_instructions = Column(JSONB, nullable=True)
    warning_signs = Column(Text, nullable=True)
    referrals = Column(JSONB, nullable=True)

    # Type
    discharge_type = Column(String(50), default="normal")  # normal, lama, absconded, death, transfer
    death_summary = Column(Text, nullable=True)
    lama_reason = Column(Text, nullable=True)

    # Status
    status = Column(String(30), default="draft")  # draft, pending_review, approved, signed, delivered
    prepared_by = Column(UUID(as_uuid=True), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True)


class IPDDietOrder(Base):
    """Diet management for admitted patients."""
    __tablename__ = "ipd_diet_orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    admission_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    diet_type = Column(String(50), nullable=False)  # regular, soft, liquid, npo, diabetic, renal, cardiac, custom
    special_instructions = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    meal_preference = Column(String(20), default="veg")  # veg, non_veg, vegan, jain
    texture = Column(String(30), nullable=True)  # normal, pureed, chopped, minced
    fluid_restriction = Column(String(50), nullable=True)
    supplements = Column(JSONB, nullable=True)
    start_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    ordered_by = Column(UUID(as_uuid=True), nullable=False)
    ordered_by_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class IPDConsentForm(Base):
    """Digital consent forms for IPD procedures."""
    __tablename__ = "ipd_consent_forms"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    admission_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    consent_type = Column(String(50), nullable=False)  # admission, procedure, surgery, anesthesia, blood_transfusion, research, general
    consent_template_id = Column(UUID(as_uuid=True), nullable=True)
    consent_details = Column(Text, nullable=True)
    procedure_name = Column(String(255), nullable=True)
    risks_explained = Column(Boolean, default=False)
    alternatives_explained = Column(Boolean, default=False)
    patient_signature = Column(Text, nullable=True)  # Base64 signature
    witness_name = Column(String(255), nullable=True)
    witness_signature = Column(Text, nullable=True)
    obtained_by = Column(UUID(as_uuid=True), nullable=False)
    obtained_by_name = Column(String(255), nullable=True)
    status = Column(String(30), default="pending")  # pending, signed, revoked
    signed_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
