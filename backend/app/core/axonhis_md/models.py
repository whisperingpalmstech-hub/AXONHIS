"""
AxonHIS MD — SQLAlchemy Models.

Baseline PostgreSQL-oriented schema for the Unified Clinical Practice + Health ATM Platform.
Covers organizations, facilities, specialty profiles, clinicians, patients,
consent, channels, appointments, encounters, clinical notes, diagnosis,
orders, prescriptions, devices, observations, documents, sharing,
payers, billing, integration events, and audit trail.
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Numeric, Date, DateTime,
    ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


# ─── Organization ────────────────────────────────────────────────────────────

class MdOrganization(Base):
    __tablename__ = "md_organization"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_organization.organization_id"), nullable=True
    )
    organization_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    facilities: Mapped[List["MdFacility"]] = relationship(back_populates="organization", lazy="selectin")
    clinicians: Mapped[List["MdClinician"]] = relationship(back_populates="organization", lazy="selectin")
    channels: Mapped[List["MdChannel"]] = relationship(back_populates="organization", lazy="selectin")


# ─── Facility ────────────────────────────────────────────────────────────────

class MdFacility(Base):
    __tablename__ = "md_facility"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_md_facility_org_code"),
    )

    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_organization.organization_id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    facility_type: Mapped[str] = mapped_column(String(50), nullable=False)
    timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organization: Mapped["MdOrganization"] = relationship(back_populates="facilities")


# ─── Specialty Profile ───────────────────────────────────────────────────────

class MdSpecialtyProfile(Base):
    __tablename__ = "md_specialty_profile"

    specialty_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ui_config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    history_template_json: Mapped[dict] = mapped_column(JSON, default=dict)
    exam_template_json: Mapped[dict] = mapped_column(JSON, default=dict)
    ai_config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    document_template_json: Mapped[dict] = mapped_column(JSON, default=dict)
    active_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─── Clinician ───────────────────────────────────────────────────────────────

class MdClinician(Base):
    __tablename__ = "md_clinician"

    clinician_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_organization.organization_id"), nullable=False
    )
    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_facility.facility_id"), nullable=True
    )
    specialty_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_specialty_profile.specialty_profile_id"), nullable=True
    )
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mobile_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    clinician_type: Mapped[str] = mapped_column(String(50), nullable=False, default="DOCTOR")
    active_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organization: Mapped["MdOrganization"] = relationship(back_populates="clinicians")
    specialty: Mapped[Optional["MdSpecialtyProfile"]] = relationship(lazy="selectin")


# ─── Patient ─────────────────────────────────────────────────────────────────

class MdPatient(Base):
    __tablename__ = "md_patient"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    enterprise_patient_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_organization.organization_id"), nullable=False
    )
    mrn: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dob: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sex: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mobile_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    preferred_language: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    deceased_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    identifiers: Mapped[List["MdPatientIdentifier"]] = relationship(back_populates="patient", cascade="all, delete-orphan", lazy="selectin")
    consent_profile: Mapped[Optional["MdConsentProfile"]] = relationship(back_populates="patient", uselist=False, lazy="selectin")
    documents: Mapped[List["MdDocument"]] = relationship(back_populates="patient", lazy="selectin")
    share_grants: Mapped[List["MdShareGrant"]] = relationship(back_populates="patient", lazy="selectin")
    coverages: Mapped[List["MdCoverage"]] = relationship(back_populates="patient", lazy="selectin")


# ─── Patient Identifier ─────────────────────────────────────────────────────

class MdPatientIdentifier(Base):
    __tablename__ = "md_patient_identifier"
    __table_args__ = (
        UniqueConstraint("identifier_type", "identifier_value", name="uq_md_patient_id_type_val"),
    )

    patient_identifier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_patient.patient_id", ondelete="CASCADE"), nullable=False
    )
    identifier_type: Mapped[str] = mapped_column(String(50), nullable=False)
    identifier_value: Mapped[str] = mapped_column(String(255), nullable=False)
    issuing_authority: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    active_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    verified_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["MdPatient"] = relationship(back_populates="identifiers")


# ─── Consent Profile ────────────────────────────────────────────────────────

class MdConsentProfile(Base):
    __tablename__ = "md_consent_profile"

    consent_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_patient.patient_id", ondelete="CASCADE"), unique=True, nullable=False
    )
    default_share_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="ASK_EACH_TIME")
    allow_summary_share: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allow_full_record_share: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sensitive_category_rules: Mapped[dict] = mapped_column(JSON, default=dict)
    marketing_contact_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patient: Mapped["MdPatient"] = relationship(back_populates="consent_profile")


# ─── Channel ────────────────────────────────────────────────────────────────

class MdChannel(Base):
    __tablename__ = "md_channel"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_md_channel_org_code"),
    )

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_organization.organization_id"), nullable=False
    )
    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_facility.facility_id"), nullable=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")

    organization: Mapped["MdOrganization"] = relationship(back_populates="channels")


# ─── Appointment ─────────────────────────────────────────────────────────────

class MdAppointment(Base):
    __tablename__ = "md_appointment"

    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_organization.organization_id"), nullable=False
    )
    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_facility.facility_id"), nullable=True
    )
    channel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_channel.channel_id"), nullable=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_patient.patient_id"), nullable=False
    )
    clinician_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_clinician.clinician_id"), nullable=True
    )
    specialty_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_specialty_profile.specialty_profile_id"), nullable=True
    )
    appointment_mode: Mapped[str] = mapped_column(String(30), nullable=False)  # IN_PERSON, TELECONSULT, HEALTH_ATM, HYBRID
    appointment_type: Mapped[str] = mapped_column(String(30), nullable=False)  # NEW, FOLLOW_UP, EMERGENCY, WALK_IN
    slot_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    slot_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    booking_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="BOOKED")
    reason_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patient: Mapped["MdPatient"] = relationship(lazy="selectin")
    clinician: Mapped[Optional["MdClinician"]] = relationship(lazy="selectin")
    specialty: Mapped[Optional["MdSpecialtyProfile"]] = relationship(lazy="selectin")


# ─── Encounter ───────────────────────────────────────────────────────────────

class MdEncounter(Base):
    __tablename__ = "md_encounter"

    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_organization.organization_id"), nullable=False
    )
    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_facility.facility_id"), nullable=True
    )
    appointment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_appointment.appointment_id"), nullable=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_patient.patient_id"), nullable=False
    )
    clinician_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_clinician.clinician_id"), nullable=True
    )
    specialty_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_specialty_profile.specialty_profile_id"), nullable=True
    )
    encounter_mode: Mapped[str] = mapped_column(String(30), nullable=False)  # IN_PERSON, TELECONSULT, HEALTH_ATM, HYBRID
    encounter_status: Mapped[str] = mapped_column(String(30), nullable=False, default="OPEN")
    chief_complaint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patient: Mapped["MdPatient"] = relationship(lazy="selectin")
    clinician: Mapped[Optional["MdClinician"]] = relationship(lazy="selectin")
    specialty: Mapped[Optional["MdSpecialtyProfile"]] = relationship(lazy="selectin")
    notes: Mapped[List["MdEncounterNote"]] = relationship(back_populates="encounter", cascade="all, delete-orphan", lazy="selectin")
    diagnoses: Mapped[List["MdDiagnosis"]] = relationship(back_populates="encounter", cascade="all, delete-orphan", lazy="selectin")
    service_requests: Mapped[List["MdServiceRequest"]] = relationship(back_populates="encounter", cascade="all, delete-orphan", lazy="selectin")
    medication_requests: Mapped[List["MdMedicationRequest"]] = relationship(back_populates="encounter", cascade="all, delete-orphan", lazy="selectin")
    device_results: Mapped[List["MdDeviceResult"]] = relationship(back_populates="encounter", cascade="all, delete-orphan", lazy="selectin")
    observations: Mapped[List["MdObservation"]] = relationship(back_populates="encounter", cascade="all, delete-orphan", lazy="selectin")


# ─── Encounter Note ──────────────────────────────────────────────────────────

class MdEncounterNote(Base):
    __tablename__ = "md_encounter_note"

    encounter_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=False
    )
    note_type: Mapped[str] = mapped_column(String(50), nullable=False)  # HISTORY, EXAM, PROGRESS, PROCEDURE, SUMMARY
    structured_json: Mapped[dict] = mapped_column(JSON, default=dict)
    narrative_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authored_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    authored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    encounter: Mapped["MdEncounter"] = relationship(back_populates="notes")


# ─── Diagnosis ───────────────────────────────────────────────────────────────

class MdDiagnosis(Base):
    __tablename__ = "md_diagnosis"

    diagnosis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=False
    )
    diagnosis_type: Mapped[str] = mapped_column(String(30), nullable=False)  # PRIMARY, SECONDARY, DIFFERENTIAL
    diagnosis_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    diagnosis_display: Mapped[str] = mapped_column(String(255), nullable=False)
    probability_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 3), nullable=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default="CLINICIAN")
    accepted_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    encounter: Mapped["MdEncounter"] = relationship(back_populates="diagnoses")


# ─── Service Request ────────────────────────────────────────────────────────

class MdServiceRequest(Base):
    __tablename__ = "md_service_request"

    service_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=False
    )
    request_type: Mapped[str] = mapped_column(String(30), nullable=False)  # LAB, IMAGING, PROCEDURE, REFERRAL
    category: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # DIAGNOSTIC, THERAPEUTIC, PREVENTIVE, MONITORING
    catalog_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    catalog_name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ORDERED")
    request_payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    encounter: Mapped["MdEncounter"] = relationship(back_populates="service_requests")


# ─── Medication Request ─────────────────────────────────────────────────────

class MdMedicationRequest(Base):
    __tablename__ = "md_medication_request"

    medication_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=False
    )
    medication_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    medication_name: Mapped[str] = mapped_column(String(255), nullable=False)
    route: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dose: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    otc_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    formulary_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default="CLINICIAN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    encounter: Mapped["MdEncounter"] = relationship(back_populates="medication_requests")


# ─── Device ──────────────────────────────────────────────────────────────────

class MdDevice(Base):
    __tablename__ = "md_device"
    __table_args__ = (
        UniqueConstraint("organization_id", "device_code", name="uq_md_device_org_code"),
    )

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_organization.organization_id"), nullable=False
    )
    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_facility.facility_id"), nullable=True
    )
    device_code: Mapped[str] = mapped_column(String(100), nullable=False)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_class: Mapped[str] = mapped_column(String(100), nullable=False)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    integration_method: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


# ─── Device Result ───────────────────────────────────────────────────────────

class MdDeviceResult(Base):
    __tablename__ = "md_device_result"

    device_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_device.device_id"), nullable=False
    )
    operator_user_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    result_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_uri: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    interpretation_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNREVIEWED")
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    encounter: Mapped["MdEncounter"] = relationship(back_populates="device_results")
    device: Mapped["MdDevice"] = relationship(lazy="selectin")


# ─── Observation ─────────────────────────────────────────────────────────────

class MdObservation(Base):
    __tablename__ = "md_observation"

    observation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=False
    )
    device_result_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_device_result.device_result_id"), nullable=True
    )
    observation_code: Mapped[str] = mapped_column(String(100), nullable=False)
    observation_display: Mapped[str] = mapped_column(String(255), nullable=False)
    value_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    value_numeric: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="FINAL")
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    encounter: Mapped["MdEncounter"] = relationship(back_populates="observations")


# ─── Document ────────────────────────────────────────────────────────────────

class MdDocument(Base):
    __tablename__ = "md_document"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_patient.patient_id", ondelete="CASCADE"), nullable=False
    )
    encounter_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id"), nullable=True
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storage_uri: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    sensitive_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    share_sensitivity: Mapped[str] = mapped_column(String(30), nullable=False, default="STANDARD")
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["MdPatient"] = relationship(back_populates="documents")


# ─── Share Grant ─────────────────────────────────────────────────────────────

class MdShareGrant(Base):
    __tablename__ = "md_share_grant"

    share_grant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_patient.patient_id", ondelete="CASCADE"), nullable=False
    )
    grant_method: Mapped[str] = mapped_column(String(30), nullable=False)  # QR_CODE, SECURE_LINK, DIRECT
    grantee_type: Mapped[str] = mapped_column(String(30), nullable=False)  # DOCTOR, HOSPITAL, INSURANCE, FAMILY
    grantee_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    scope_type: Mapped[str] = mapped_column(String(30), nullable=False)  # FULL, SUMMARY, ENCOUNTER, DOCUMENT
    scope_json: Mapped[dict] = mapped_column(JSON, default=dict)
    qr_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    secure_link_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["MdPatient"] = relationship(back_populates="share_grants")
    access_logs: Mapped[List["MdShareAccessLog"]] = relationship(back_populates="share_grant", cascade="all, delete-orphan", lazy="selectin")


# ─── Share Access Log ────────────────────────────────────────────────────────

class MdShareAccessLog(Base):
    __tablename__ = "md_share_access_log"

    share_access_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    share_grant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_share_grant.share_grant_id", ondelete="CASCADE"), nullable=False
    )
    accessed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    access_channel: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    access_result: Mapped[str] = mapped_column(String(30), nullable=False)
    accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    share_grant: Mapped["MdShareGrant"] = relationship(back_populates="access_logs")


# ─── Payer ───────────────────────────────────────────────────────────────────

class MdPayer(Base):
    __tablename__ = "md_payer"
    __table_args__ = (
        UniqueConstraint("organization_id", "payer_code", name="uq_md_payer_org_code"),
    )

    payer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_organization.organization_id"), nullable=False
    )
    payer_code: Mapped[str] = mapped_column(String(100), nullable=False)
    payer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    payer_type: Mapped[str] = mapped_column(String(50), nullable=False)
    active_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


# ─── Coverage ────────────────────────────────────────────────────────────────

class MdCoverage(Base):
    __tablename__ = "md_coverage"

    coverage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_patient.patient_id", ondelete="CASCADE"), nullable=False
    )
    payer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_payer.payer_id"), nullable=False
    )
    policy_number: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    member_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    plan_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    effective_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    active_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["MdPatient"] = relationship(back_populates="coverages")
    payer: Mapped["MdPayer"] = relationship(lazy="selectin")


# ─── Billing Invoice ────────────────────────────────────────────────────────

class MdBillingInvoice(Base):
    __tablename__ = "md_billing_invoice"

    billing_invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_organization.organization_id"), nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_patient.patient_id"), nullable=False
    )
    encounter_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id"), nullable=True
    )
    coverage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_coverage.coverage_id"), nullable=True
    )
    invoice_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["MdPatient"] = relationship(lazy="selectin")
    line_items: Mapped[List["MdBillingLineItem"]] = relationship(back_populates="invoice", cascade="all, delete-orphan", lazy="selectin")


# ─── Billing Line Item ──────────────────────────────────────────────────────

class MdBillingLineItem(Base):
    __tablename__ = "md_billing_line_item"

    billing_line_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    billing_invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_billing_invoice.billing_invoice_id", ondelete="CASCADE"), nullable=False
    )
    line_type: Mapped[str] = mapped_column(String(30), nullable=False)
    catalog_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)

    invoice: Mapped["MdBillingInvoice"] = relationship(back_populates="line_items")


# ─── Integration Event ──────────────────────────────────────────────────────

class MdIntegrationEvent(Base):
    __tablename__ = "md_integration_event"

    integration_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_organization.organization_id"), nullable=True
    )
    source_system: Mapped[str] = mapped_column(String(100), nullable=False)
    target_system: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ─── Audit Event ─────────────────────────────────────────────────────────────

class MdAuditEvent(Base):
    __tablename__ = "md_audit_event"

    audit_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_organization.organization_id"), nullable=True
    )
    actor_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_patient.patient_id"), nullable=True
    )
    encounter_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id"), nullable=True
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_status: Mapped[str] = mapped_column(String(30), nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
