import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class RpiwPatientSummary(Base):
    """Core table holding high-level aggregated patient summary."""
    __tablename__ = "rpiw_patient_summary"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_uhid = Column(String, nullable=False, index=True)
    admission_number = Column(String, nullable=True, index=True)
    visit_id = Column(String, nullable=True, index=True)
    
    chief_issue = Column(Text, nullable=True)
    primary_diagnosis = Column(String, nullable=True)
    current_clinical_status = Column(String, nullable=True)
    
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_updated_by = Column(String, nullable=True)  # System or specific user ID


class RpiwSummarySource(Base):
    """Tracks which external sources and records were used to build the summary."""
    __tablename__ = "rpiw_summary_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    summary_id = Column(UUID(as_uuid=True), ForeignKey("rpiw_patient_summary.id", ondelete="CASCADE"), nullable=False, index=True)
    source_module = Column(String, nullable=False)  # IPD, OPD, LIS, Pharmacy, EHR, etc.
    source_record_id = Column(String, nullable=False)
    timestamp_aggregated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RpiwSummaryAlert(Base):
    """Holds detected clinical risks (critical labs, allergy conflicts)."""
    __tablename__ = "rpiw_summary_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    summary_id = Column(UUID(as_uuid=True), ForeignKey("rpiw_patient_summary.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String, nullable=False)  # critical_lab, abnormal_vital, allergy_conflict, drug_interaction
    severity = Column(String, nullable=False)  # low, medium, high, critical
    message = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class RpiwSummaryTask(Base):
    """Tracks incomplete clinical tasks specifically in the context of the summary view."""
    __tablename__ = "rpiw_summary_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    summary_id = Column(UUID(as_uuid=True), ForeignKey("rpiw_patient_summary.id", ondelete="CASCADE"), nullable=False, index=True)
    task_category = Column(String, nullable=False)  # lab_test, imaging, medication_admin, procedure
    description = Column(String, nullable=False)
    status = Column(String, default="Pending")  # Pending, In Progress, Completed, Cancelled
    due_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RpiwSummaryVital(Base):
    """Extracted recent vitals data to display trends."""
    __tablename__ = "rpiw_summary_vitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    summary_id = Column(UUID(as_uuid=True), ForeignKey("rpiw_patient_summary.id", ondelete="CASCADE"), nullable=False, index=True)
    vital_sign = Column(String, nullable=False)  # bp, heart_rate, temperature, spo2
    value = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    is_abnormal = Column(Boolean, default=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False)


class RpiwSummaryMedication(Base):
    """Concise view of active medications."""
    __tablename__ = "rpiw_summary_medications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    summary_id = Column(UUID(as_uuid=True), ForeignKey("rpiw_patient_summary.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    route = Column(String, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
