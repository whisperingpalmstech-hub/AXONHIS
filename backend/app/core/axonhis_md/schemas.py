"""
AxonHIS MD — Pydantic Schemas (request / response models).
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any
from pydantic import BaseModel, Field
import uuid


# ─── Organization ──────────────────────────────────────

class OrganizationCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    parent_organization_id: Optional[uuid.UUID] = None
    organization_type: str = Field(..., max_length=50)

class OrganizationOut(BaseModel):
    organization_id: uuid.UUID
    code: str
    name: str
    parent_organization_id: Optional[uuid.UUID] = None
    organization_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# ─── Facility ──────────────────────────────────────────

class FacilityCreate(BaseModel):
    organization_id: uuid.UUID
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    facility_type: str = Field(..., max_length=50)
    timezone: Optional[str] = None

class FacilityOut(BaseModel):
    facility_id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    name: str
    facility_type: str
    timezone: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# ─── Specialty Profile ────────────────────────────────

class SpecialtyProfileCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    ui_config_json: dict = {}
    history_template_json: dict = {}
    exam_template_json: dict = {}
    ai_config_json: dict = {}
    document_template_json: dict = {}

class SpecialtyProfileOut(BaseModel):
    specialty_profile_id: uuid.UUID
    code: str
    name: str
    version_no: int
    description: Optional[str] = None
    ui_config_json: dict
    history_template_json: dict
    exam_template_json: dict
    ai_config_json: dict
    document_template_json: dict
    active_flag: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# ─── Clinician ─────────────────────────────────────────

class ClinicianCreate(BaseModel):
    organization_id: uuid.UUID
    facility_id: Optional[uuid.UUID] = None
    specialty_profile_id: Optional[uuid.UUID] = None
    code: Optional[str] = None
    display_name: str = Field(..., max_length=255)
    mobile_number: Optional[str] = None
    email: Optional[str] = None
    clinician_type: str = "DOCTOR"

class ClinicianOut(BaseModel):
    clinician_id: uuid.UUID
    organization_id: uuid.UUID
    facility_id: Optional[uuid.UUID] = None
    specialty_profile_id: Optional[uuid.UUID] = None
    code: Optional[str] = None
    display_name: str
    mobile_number: Optional[str] = None
    email: Optional[str] = None
    clinician_type: str
    active_flag: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# ─── Patient ──────────────────────────────────────────

class PatientIdentifierCreate(BaseModel):
    identifier_type: str
    identifier_value: str
    issuing_authority: Optional[str] = None

class PatientIdentifierOut(BaseModel):
    patient_identifier_id: uuid.UUID
    identifier_type: str
    identifier_value: str
    issuing_authority: Optional[str] = None
    active_flag: bool
    verified_flag: bool
    class Config:
        from_attributes = True

class ConsentProfileCreate(BaseModel):
    default_share_mode: str = "ASK_EACH_TIME"
    allow_summary_share: bool = True
    allow_full_record_share: bool = False
    sensitive_category_rules: dict = {}
    marketing_contact_allowed: bool = False

class ConsentProfileOut(BaseModel):
    consent_profile_id: uuid.UUID
    default_share_mode: str
    allow_summary_share: bool
    allow_full_record_share: bool
    sensitive_category_rules: dict
    marketing_contact_allowed: bool
    class Config:
        from_attributes = True

class PatientCreate(BaseModel):
    organization_id: uuid.UUID
    mrn: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: str = Field(..., max_length=255)
    dob: Optional[date] = None
    sex: Optional[str] = None
    mobile_number: Optional[str] = None
    email: Optional[str] = None
    preferred_language: Optional[str] = None
    identifiers: List[PatientIdentifierCreate] = []
    consent: Optional[ConsentProfileCreate] = None

class PatientOut(BaseModel):
    patient_id: uuid.UUID
    enterprise_patient_key: str
    organization_id: uuid.UUID
    mrn: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: str
    dob: Optional[date] = None
    sex: Optional[str] = None
    mobile_number: Optional[str] = None
    email: Optional[str] = None
    preferred_language: Optional[str] = None
    deceased_flag: bool
    status: str
    identifiers: List[PatientIdentifierOut] = []
    consent_profile: Optional[ConsentProfileOut] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# ─── Channel ──────────────────────────────────────────

class ChannelCreate(BaseModel):
    organization_id: uuid.UUID
    facility_id: Optional[uuid.UUID] = None
    code: str
    name: str
    channel_type: str  # CLINIC, TELECONSULT, HEALTH_ATM, HYBRID

class ChannelOut(BaseModel):
    channel_id: uuid.UUID
    organization_id: uuid.UUID
    facility_id: Optional[uuid.UUID] = None
    code: str
    name: str
    channel_type: str
    status: str
    class Config:
        from_attributes = True


# ─── Appointment ───────────────────────────────────────

class AppointmentCreate(BaseModel):
    organization_id: uuid.UUID
    facility_id: Optional[uuid.UUID] = None
    channel_id: Optional[uuid.UUID] = None
    patient_id: uuid.UUID
    clinician_id: Optional[uuid.UUID] = None
    specialty_profile_id: Optional[uuid.UUID] = None
    appointment_mode: str  # IN_PERSON, TELECONSULT, HEALTH_ATM, HYBRID
    appointment_type: str  # NEW, FOLLOW_UP, EMERGENCY, WALK_IN
    slot_start: datetime
    slot_end: datetime
    booking_source: Optional[str] = None
    reason_text: Optional[str] = None

class AppointmentOut(BaseModel):
    appointment_id: uuid.UUID
    organization_id: uuid.UUID
    facility_id: Optional[uuid.UUID] = None
    channel_id: Optional[uuid.UUID] = None
    patient_id: uuid.UUID
    clinician_id: Optional[uuid.UUID] = None
    specialty_profile_id: Optional[uuid.UUID] = None
    appointment_mode: str
    appointment_type: str
    slot_start: datetime
    slot_end: datetime
    status: str
    booking_source: Optional[str] = None
    reason_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    encounter_id: Optional[uuid.UUID] = None
    # nested
    patient_name: Optional[str] = None
    clinician_name: Optional[str] = None
    class Config:
        from_attributes = True


# ─── Encounter ─────────────────────────────────────────

class EncounterCreate(BaseModel):
    organization_id: uuid.UUID
    facility_id: Optional[uuid.UUID] = None
    appointment_id: Optional[uuid.UUID] = None
    patient_id: uuid.UUID
    clinician_id: Optional[uuid.UUID] = None
    specialty_profile_id: Optional[uuid.UUID] = None
    encounter_mode: str
    chief_complaint: Optional[str] = None
    created_by: Optional[str] = None

class EncounterOut(BaseModel):
    encounter_id: uuid.UUID
    organization_id: uuid.UUID
    facility_id: Optional[uuid.UUID] = None
    appointment_id: Optional[uuid.UUID] = None
    patient_id: uuid.UUID
    clinician_id: Optional[uuid.UUID] = None
    specialty_profile_id: Optional[uuid.UUID] = None
    encounter_mode: str
    encounter_status: str
    chief_complaint: Optional[str] = None
    started_at: datetime
    closed_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: datetime
    patient_name: Optional[str] = None
    clinician_name: Optional[str] = None
    class Config:
        from_attributes = True


# ─── Encounter Note ───────────────────────────────────

class EncounterNoteCreate(BaseModel):
    encounter_id: uuid.UUID
    note_type: str  # HISTORY, EXAM, PROGRESS, PROCEDURE, SUMMARY
    structured_json: dict = {}
    narrative_text: Optional[str] = None
    authored_by: Optional[str] = None

class EncounterNoteOut(BaseModel):
    encounter_note_id: uuid.UUID
    encounter_id: uuid.UUID
    note_type: str
    structured_json: dict
    narrative_text: Optional[str] = None
    authored_by: Optional[str] = None
    authored_at: datetime
    class Config:
        from_attributes = True


# ─── Diagnosis ─────────────────────────────────────────

class DiagnosisCreate(BaseModel):
    encounter_id: uuid.UUID
    diagnosis_type: str  # PRIMARY, SECONDARY, DIFFERENTIAL
    diagnosis_code: Optional[str] = None
    diagnosis_display: str
    probability_score: Optional[float] = None
    source_type: str = "CLINICIAN"

class DiagnosisOut(BaseModel):
    diagnosis_id: uuid.UUID
    encounter_id: uuid.UUID
    diagnosis_type: str
    diagnosis_code: Optional[str] = None
    diagnosis_display: str
    probability_score: Optional[float] = None
    source_type: str
    accepted_flag: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ─── Service Request ──────────────────────────────────

class ServiceRequestCreate(BaseModel):
    encounter_id: uuid.UUID
    request_type: str  # LAB, IMAGING, PROCEDURE, REFERRAL
    category: Optional[str] = None  # DIAGNOSTIC, THERAPEUTIC, PREVENTIVE, MONITORING
    catalog_code: Optional[str] = None
    catalog_name: str
    priority: Optional[str] = None
    request_payload_json: dict = {}

class ServiceRequestOut(BaseModel):
    service_request_id: uuid.UUID
    encounter_id: uuid.UUID
    request_type: str
    category: Optional[str] = None
    catalog_code: Optional[str] = None
    catalog_name: str
    priority: Optional[str] = None
    status: str
    request_payload_json: dict
    created_at: datetime
    class Config:
        from_attributes = True


# ─── Medication Request ───────────────────────────────

class MedicationRequestCreate(BaseModel):
    encounter_id: uuid.UUID
    medication_code: Optional[str] = None
    medication_name: str
    route: Optional[str] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    otc_flag: bool = False
    formulary_flag: bool = True
    source_type: str = "CLINICIAN"

class MedicationRequestOut(BaseModel):
    medication_request_id: uuid.UUID
    encounter_id: uuid.UUID
    medication_code: Optional[str] = None
    medication_name: str
    route: Optional[str] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    otc_flag: bool
    formulary_flag: bool
    source_type: str
    created_at: datetime
    class Config:
        from_attributes = True


# ─── Device ────────────────────────────────────────────

class DeviceCreate(BaseModel):
    organization_id: uuid.UUID
    facility_id: Optional[uuid.UUID] = None
    device_code: str
    device_name: str
    device_class: str
    manufacturer: Optional[str] = None
    integration_method: Optional[str] = None
    metadata_json: dict = {}

class DeviceOut(BaseModel):
    device_id: uuid.UUID
    organization_id: uuid.UUID
    facility_id: Optional[uuid.UUID] = None
    device_code: str
    device_name: str
    device_class: str
    manufacturer: Optional[str] = None
    integration_method: Optional[str] = None
    status: str
    metadata_json: dict
    class Config:
        from_attributes = True


# ─── Device Result ─────────────────────────────────────

class DeviceResultCreate(BaseModel):
    encounter_id: uuid.UUID
    device_id: uuid.UUID
    operator_user_ref: Optional[str] = None
    result_type: str
    payload_json: dict = {}
    raw_uri: Optional[str] = None

class DeviceResultOut(BaseModel):
    device_result_id: uuid.UUID
    encounter_id: uuid.UUID
    device_id: uuid.UUID
    operator_user_ref: Optional[str] = None
    result_type: str
    payload_json: dict
    raw_uri: Optional[str] = None
    interpretation_status: str
    captured_at: datetime
    class Config:
        from_attributes = True


# ─── Observation ───────────────────────────────────────

class ObservationCreate(BaseModel):
    encounter_id: uuid.UUID
    device_result_id: Optional[uuid.UUID] = None
    observation_code: str
    observation_display: str
    value_text: Optional[str] = None
    value_numeric: Optional[float] = None
    unit: Optional[str] = None

class ObservationOut(BaseModel):
    observation_id: uuid.UUID
    encounter_id: uuid.UUID
    device_result_id: Optional[uuid.UUID] = None
    observation_code: str
    observation_display: str
    value_text: Optional[str] = None
    value_numeric: Optional[float] = None
    unit: Optional[str] = None
    status: str
    effective_at: datetime
    class Config:
        from_attributes = True


# ─── Document ──────────────────────────────────────────

class DocumentCreate(BaseModel):
    patient_id: Optional[uuid.UUID] = None
    encounter_id: Optional[uuid.UUID] = None
    document_type: str
    category: Optional[str] = None
    title: str
    content_text: Optional[str] = None
    storage_uri: str
    mime_type: Optional[str] = None
    status: str = "DRAFT"
    sensitive_flag: bool = False
    share_sensitivity: str = "STANDARD"
    created_by: Optional[str] = None

class DocumentOut(BaseModel):
    document_id: uuid.UUID
    patient_id: uuid.UUID
    encounter_id: Optional[uuid.UUID] = None
    document_type: str
    category: Optional[str] = None
    title: str
    content_text: Optional[str] = None
    storage_uri: str
    mime_type: Optional[str] = None
    status: str
    sensitive_flag: bool
    share_sensitivity: str
    created_by: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


# ─── Share Grant ───────────────────────────────────────

class ShareGrantCreate(BaseModel):
    patient_id: uuid.UUID
    grant_method: str  # QR_CODE, SECURE_LINK, DIRECT
    grantee_type: str  # DOCTOR, HOSPITAL, INSURANCE, FAMILY
    grantee_reference: Optional[str] = None
    scope_type: str  # FULL, SUMMARY, ENCOUNTER, DOCUMENT
    scope_json: dict = {}
    expires_at: Optional[datetime] = None

class ShareGrantOut(BaseModel):
    share_grant_id: uuid.UUID
    patient_id: uuid.UUID
    grant_method: str
    grantee_type: str
    grantee_reference: Optional[str] = None
    scope_type: str
    scope_json: dict
    qr_token: Optional[str] = None
    secure_link_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True


# ─── Payer ─────────────────────────────────────────────

class PayerCreate(BaseModel):
    organization_id: uuid.UUID
    payer_code: str
    payer_name: str
    payer_type: str

class PayerOut(BaseModel):
    payer_id: uuid.UUID
    organization_id: uuid.UUID
    payer_code: str
    payer_name: str
    payer_type: str
    active_flag: bool
    class Config:
        from_attributes = True


# ─── Coverage ──────────────────────────────────────────

class CoverageCreate(BaseModel):
    patient_id: uuid.UUID
    payer_id: uuid.UUID
    policy_number: Optional[str] = None
    member_reference: Optional[str] = None
    plan_name: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None

class CoverageOut(BaseModel):
    coverage_id: uuid.UUID
    patient_id: uuid.UUID
    payer_id: uuid.UUID
    policy_number: Optional[str] = None
    member_reference: Optional[str] = None
    plan_name: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    active_flag: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ─── Billing ──────────────────────────────────────────

class BillingLineItemCreate(BaseModel):
    line_type: str = "SERVICE"
    catalog_reference: Optional[str] = None
    description: str
    quantity: float = 1
    unit_price: float = 0
    line_amount: float = 0

class BillingLineItemOut(BaseModel):
    billing_line_item_id: uuid.UUID
    line_type: str
    catalog_reference: Optional[str] = None
    description: str
    quantity: float
    unit_price: float
    line_amount: float
    class Config:
        from_attributes = True

class BillingInvoiceCreate(BaseModel):
    organization_id: Optional[uuid.UUID] = None
    patient_id: uuid.UUID
    encounter_id: Optional[uuid.UUID] = None
    coverage_id: Optional[uuid.UUID] = None
    currency_code: str = "USD"
    due_date: Optional[date] = None
    line_items: List[BillingLineItemCreate] = []

class BillingInvoiceOut(BaseModel):
    billing_invoice_id: uuid.UUID
    organization_id: uuid.UUID
    patient_id: uuid.UUID
    encounter_id: Optional[uuid.UUID] = None
    coverage_id: Optional[uuid.UUID] = None
    invoice_number: str
    currency_code: str
    due_date: Optional[date] = None
    total_amount: float
    status: str
    created_at: datetime
    line_items: List[BillingLineItemOut] = []
    patient_name: Optional[str] = None
    class Config:
        from_attributes = True


# ─── Integration Event ────────────────────────────────

class IntegrationEventCreate(BaseModel):
    organization_id: Optional[uuid.UUID] = None
    source_system: str
    target_system: Optional[str] = None
    resource_type: str
    resource_id: Optional[str] = None
    event_type: str
    payload_json: dict = {}
    correlation_id: Optional[str] = None

class IntegrationEventOut(BaseModel):
    integration_event_id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    source_system: str
    target_system: Optional[str] = None
    resource_type: str
    resource_id: Optional[str] = None
    event_type: str
    event_status: str
    payload_json: dict
    correlation_id: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


# ─── Audit Event ──────────────────────────────────────

class AuditEventOut(BaseModel):
    audit_event_id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    actor_ref: Optional[str] = None
    actor_role: Optional[str] = None
    patient_id: Optional[uuid.UUID] = None
    encounter_id: Optional[uuid.UUID] = None
    action_type: str
    action_status: str
    event_time: datetime
    details_json: dict
    class Config:
        from_attributes = True


# ─── Dashboard Stats ──────────────────────────────────

class MdDashboardStats(BaseModel):
    total_organizations: int = 0
    total_facilities: int = 0
    total_clinicians: int = 0
    total_patients: int = 0
    total_appointments: int = 0
    appointments_today: int = 0
    open_encounters: int = 0
    total_encounters: int = 0
    pending_service_requests: int = 0
    total_devices: int = 0
    total_documents: int = 0
    active_share_grants: int = 0
    total_invoices: int = 0
    draft_invoices: int = 0
    pending_integration_events: int = 0
    total_specialties: int = 0
