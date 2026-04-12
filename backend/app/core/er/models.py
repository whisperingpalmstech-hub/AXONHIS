"""
ER Module — Database Models
============================
Complete Emergency Room data model per FRD:
- EREncounter (urgent/normal registration)
- ERTriage (ESI-based assessment)
- ERBedAllocation (zone-based bed map)
- ERMlcCase (Medico-Legal Case)
- ERNursingScore (MEWS, SOFA, GCS, etc.)
- ERDischarge (multi-step discharge workflow)

All models include org_id for multi-tenancy.
Interconnected with: patients, encounters, wards, billing_masters, orders, pharmacy
"""
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer, Numeric,
    ForeignKey, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class TriageCategory(StrEnum):
    resuscitation = "resuscitation"  # ESI-1 (Red)
    emergent = "emergent"            # ESI-2 (Orange)
    urgent = "urgent"                # ESI-3 (Yellow)
    less_urgent = "less_urgent"      # ESI-4 (Green)
    non_urgent = "non_urgent"        # ESI-5 (Blue)
    dead = "dead"                    # DOA (Black)

class ERRegistrationType(StrEnum):
    urgent = "urgent"    # Minimal fields, temp ER number
    normal = "normal"    # Full UHID registration

class EREncounterStatus(StrEnum):
    registered = "registered"
    triaged = "triaged"
    in_treatment = "in_treatment"
    observation = "observation"
    due_for_discharge = "due_for_discharge"
    marked_for_discharge = "marked_for_discharge"
    ready_for_billing = "ready_for_billing"
    discharged = "discharged"
    transferred_to_ipd = "transferred_to_ipd"
    left_ama = "left_ama"          # Against Medical Advice
    absconded = "absconded"
    dead_on_arrival = "dead_on_arrival"

class ERZone(StrEnum):
    red = "red"         # Resuscitation
    yellow = "yellow"   # Acute care
    green = "green"     # Fast track / Minor
    peds = "peds"       # Pediatrics
    obs = "obs"         # Observation


# ════════════════════════════════════════════════════════════════
#  ER ENCOUNTER (Core ER Visit)
# ════════════════════════════════════════════════════════════════

class EREncounter(Base):
    """Core ER visit record — links patient to ER workflow."""
    __tablename__ = "er_encounters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Registration
    er_number = Column(String(50), unique=True, nullable=False)
    registration_type = Column(String(20), nullable=False, default="normal")
    patient_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Null for urgent unregistered
    encounter_id = Column(UUID(as_uuid=True), nullable=True)  # Link to encounter module

    # Patient info (minimal for urgent reg)
    patient_name = Column(String(255), nullable=False)
    patient_uhid = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)
    age_unit = Column(String(10), default="years")  # years, months, days
    gender = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)
    temp_id_description = Column(Text, nullable=True)  # Physical description for unidentified

    # Mode of arrival
    mode_of_arrival = Column(String(50), nullable=True)  # ambulance, walk_in, police, referral
    ambulance_number = Column(String(50), nullable=True)
    brought_by = Column(String(255), nullable=True)
    referral_source = Column(String(255), nullable=True)

    # Chief complaint
    chief_complaint = Column(Text, nullable=True)
    presenting_complaints = Column(JSONB, nullable=True)

    # Status & Zone
    status = Column(String(50), default="registered")
    zone = Column(String(20), nullable=True)
    priority = Column(String(30), nullable=True)  # triage category
    is_mlc = Column(Boolean, default=False)

    # Clinical flags
    is_critical = Column(Boolean, default=False)
    is_ventilator = Column(Boolean, default=False)
    is_allergy = Column(Boolean, default=False)
    allergy_details = Column(Text, nullable=True)
    has_overdue_orders = Column(Boolean, default=False)
    has_overdue_los = Column(Boolean, default=False)

    # Attending staff
    attending_doctor_id = Column(UUID(as_uuid=True), nullable=True)
    attending_doctor_name = Column(String(255), nullable=True)
    attending_nurse_id = Column(UUID(as_uuid=True), nullable=True)
    attending_nurse_name = Column(String(255), nullable=True)

    # Timestamps
    arrival_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    triage_time = Column(DateTime(timezone=True), nullable=True)
    treatment_start_time = Column(DateTime(timezone=True), nullable=True)
    discharge_time = Column(DateTime(timezone=True), nullable=True)

    # Disposition
    disposition = Column(String(50), nullable=True)  # discharge, admit_ipd, transfer, lama, doa
    disposition_department = Column(String(100), nullable=True)
    ipd_admission_id = Column(UUID(as_uuid=True), nullable=True)  # Link to IPD if transferred

    # Billing linkage
    bill_id = Column(UUID(as_uuid=True), nullable=True)  # Link to rcm_billing_master

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True)


# ════════════════════════════════════════════════════════════════
#  ER TRIAGE
# ════════════════════════════════════════════════════════════════

class ERTriage(Base):
    """ESI-based triage assessment."""
    __tablename__ = "er_triage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    er_encounter_id = Column(UUID(as_uuid=True), ForeignKey("er_encounters.id"), nullable=False)

    # ESI Assessment
    triage_category = Column(String(30), nullable=False)  # TriageCategory enum
    triage_color = Column(String(20), nullable=True)  # red, orange, yellow, green, blue, black

    # Vitals at triage
    temperature = Column(Numeric(5, 2), nullable=True)
    pulse = Column(Integer, nullable=True)
    bp_systolic = Column(Integer, nullable=True)
    bp_diastolic = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    spo2 = Column(Numeric(5, 2), nullable=True)
    gcs_score = Column(Integer, nullable=True)
    pain_score = Column(Integer, nullable=True)
    blood_glucose = Column(Numeric(7, 2), nullable=True)

    # ABCDE Assessment
    airway = Column(String(50), nullable=True)
    breathing = Column(String(50), nullable=True)
    circulation = Column(String(50), nullable=True)
    disability = Column(String(50), nullable=True)
    exposure = Column(String(50), nullable=True)

    # History
    allergies = Column(Text, nullable=True)
    current_medications = Column(Text, nullable=True)
    past_medical_history = Column(Text, nullable=True)
    last_meal = Column(String(100), nullable=True)
    immunization_status = Column(String(100), nullable=True)

    # Triage notes
    triage_notes = Column(Text, nullable=True)
    triaged_by = Column(UUID(as_uuid=True), nullable=False)
    triaged_by_name = Column(String(255), nullable=True)
    triaged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ════════════════════════════════════════════════════════════════
#  ER BED ALLOCATION (Zone-based)
# ════════════════════════════════════════════════════════════════

class ERBed(Base):
    """ER bed/bay — zone-based allocation map."""
    __tablename__ = "er_beds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    bed_code = Column(String(50), nullable=False)
    zone = Column(String(20), nullable=False)  # ERZone enum
    bed_type = Column(String(50), default="stretcher")  # stretcher, bed, recliner, chair
    is_monitored = Column(Boolean, default=False)
    has_ventilator = Column(Boolean, default=False)

    # Status
    status = Column(String(30), default="available")  # available, occupied, cleaning, reserved, maintenance
    occupied_by_er_encounter_id = Column(UUID(as_uuid=True), nullable=True)
    patient_gender = Column(String(20), nullable=True)

    occupied_since = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)


# ════════════════════════════════════════════════════════════════
#  MLC (Medico-Legal Case)
# ════════════════════════════════════════════════════════════════

class ERMlcCase(Base):
    """Medico-Legal Case management linked to ER encounter."""
    __tablename__ = "er_mlc_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    er_encounter_id = Column(UUID(as_uuid=True), ForeignKey("er_encounters.id"), nullable=False)

    mlc_number = Column(String(50), unique=True, nullable=False)
    mlc_type = Column(String(50), nullable=True)  # assault, rta, poisoning, burns, sexual_assault, etc.
    priority = Column(String(20), default="medium")  # high, medium, low

    # Police details
    police_station = Column(String(255), nullable=True)
    police_officer_name = Column(String(255), nullable=True)
    police_officer_badge = Column(String(100), nullable=True)
    fir_number = Column(String(100), nullable=True)
    buckle_number = Column(String(100), nullable=True)

    # Injuries
    injury_description = Column(Text, nullable=True)
    injury_details = Column(JSONB, nullable=True)  # [{type, location, severity}]

    # Legal documentation
    legal_notes = Column(Text, nullable=True)
    documents = Column(JSONB, nullable=True)  # Uploaded legal docs

    status = Column(String(30), default="active")  # active, closed, transferred
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True)


# ════════════════════════════════════════════════════════════════
#  NURSING SCORING SYSTEMS
# ════════════════════════════════════════════════════════════════

class ERNursingScore(Base):
    """Clinical scoring systems (MEWS, SOFA, APACHE-II, GCS, Pediatric)."""
    __tablename__ = "er_nursing_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    er_encounter_id = Column(UUID(as_uuid=True), ForeignKey("er_encounters.id"), nullable=False)

    score_type = Column(String(30), nullable=False)  # mews, sofa, apache_ii, gcs, pediatric, fall_risk, pain
    total_score = Column(Integer, nullable=False)
    risk_level = Column(String(30), nullable=True)  # low, moderate, high, critical
    score_components = Column(JSONB, nullable=True)  # Breakdown of individual components
    interpretation = Column(Text, nullable=True)

    scored_by = Column(UUID(as_uuid=True), nullable=False)
    scored_by_name = Column(String(255), nullable=True)
    scored_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ════════════════════════════════════════════════════════════════
#  ER ORDERS (Quick orders within ER)
# ════════════════════════════════════════════════════════════════

class EROrder(Base):
    """Quick clinical orders placed during ER encounter. Links to main orders module."""
    __tablename__ = "er_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    er_encounter_id = Column(UUID(as_uuid=True), ForeignKey("er_encounters.id"), nullable=False)

    order_type = Column(String(30), nullable=False)  # lab, radiology, medication, procedure, consult
    order_id = Column(UUID(as_uuid=True), nullable=True)  # Link to main orders module
    order_description = Column(Text, nullable=False)
    priority = Column(String(20), default="stat")  # stat, urgent, routine
    status = Column(String(30), default="ordered")  # ordered, in_progress, completed, cancelled

    ordered_by = Column(UUID(as_uuid=True), nullable=False)
    ordered_by_name = Column(String(255), nullable=True)
    ordered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)


# ════════════════════════════════════════════════════════════════
#  ER DISCHARGE
# ════════════════════════════════════════════════════════════════

class ERDischarge(Base):
    """Formal ER discharge record — links to billing settlement."""
    __tablename__ = "er_discharges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    er_encounter_id = Column(UUID(as_uuid=True), ForeignKey("er_encounters.id"), nullable=False)

    # Discharge classification
    discharge_type = Column(String(50), nullable=False)  # normal, dama, lama, death, absconded
    discharge_summary = Column(Text, nullable=True)
    follow_up_instructions = Column(Text, nullable=True)
    follow_up_date = Column(DateTime(timezone=True), nullable=True)

    # Billing clearance
    billing_cleared = Column(Boolean, default=False)
    total_amount = Column(Numeric(12, 2), nullable=True)
    paid_amount = Column(Numeric(12, 2), nullable=True)
    payment_mode = Column(String(50), nullable=True)  # cash, card, upi, cheque, insurance

    # Final disposition
    disposition = Column(String(50), nullable=True)  # home, ipd_admit, transfer_other, morgue
    destination_department = Column(String(100), nullable=True)

    # Bed release
    bed_vacated = Column(Boolean, default=False)
    bed_id = Column(UUID(as_uuid=True), nullable=True)

    discharged_by = Column(UUID(as_uuid=True), nullable=False)
    discharged_by_name = Column(String(255), nullable=True)
    discharged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ════════════════════════════════════════════════════════════════
#  ER CLINICAL NOTES (Nursing Cover Sheet)
# ════════════════════════════════════════════════════════════════

class ERClinicalNote(Base):
    """Clinical documentation — complaints, history, exam, shift notes, SOAP."""
    __tablename__ = "er_clinical_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    er_encounter_id = Column(UUID(as_uuid=True), ForeignKey("er_encounters.id"), nullable=False)

    note_type = Column(String(50), nullable=False)
    # complaint, history, examination, observation, shift_note, soap, procedure_note

    # Structured content
    content = Column(Text, nullable=True)
    structured_data = Column(JSONB, nullable=True)
    # For complaint: {icpc_code, description, onset, severity}
    # For history: {medical_hx, surgical_hx, allergies, medications, lifestyle, vaccinations}
    # For examination: {vitals: {temp, pulse, bp, rr, spo2, pain}, systems_review: {...}}

    # Metadata
    authored_by = Column(UUID(as_uuid=True), nullable=False)
    authored_by_name = Column(String(255), nullable=True)
    authored_by_role = Column(String(50), nullable=True)  # doctor, nurse
    authored_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_addendum = Column(Boolean, default=False)


# ════════════════════════════════════════════════════════════════
#  ER DIAGNOSIS (ICD-10)
# ════════════════════════════════════════════════════════════════

class ERDiagnosis(Base):
    """ICD-10 coded diagnosis for ER encounter."""
    __tablename__ = "er_diagnoses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    er_encounter_id = Column(UUID(as_uuid=True), ForeignKey("er_encounters.id"), nullable=False)

    icd_code = Column(String(20), nullable=True)
    diagnosis_description = Column(Text, nullable=False)
    diagnosis_type = Column(String(30), default="working")  # working, confirmed, differential, final
    is_primary = Column(Boolean, default=False)

    recorded_by = Column(UUID(as_uuid=True), nullable=False)
    recorded_by_name = Column(String(255), nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
