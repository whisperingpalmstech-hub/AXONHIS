from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class ReportCommentTemplate(Base):
    __tablename__ = "lis_report_comments"
    id = Column(String, primary_key=True, default=generate_uuid)
    department = Column(String, index=True)
    test_code = Column(String, index=True)
    condition_rule = Column(String) # e.g. "RESULT == 'Reactive'", "VALUE > 180"
    auto_comment = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ReportTemplate(Base):
    __tablename__ = "lis_report_templates"
    id = Column(String, primary_key=True, default=generate_uuid)
    department = Column(String, unique=True, index=True)
    layout_config = Column(JSON, nullable=False) # branding elements, tables
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LabReport(Base):
    __tablename__ = "lis_reports"
    id = Column(String, primary_key=True, default=generate_uuid)
    sample_id = Column(String, index=True, nullable=False)
    test_order_id = Column(String, index=True, nullable=False)
    patient_uhid = Column(String, index=True, nullable=False)
    patient_name = Column(String, nullable=False)
    visit_id = Column(String, nullable=True)
    department = Column(String, index=True)
    test_details = Column(JSON, nullable=False) # list of params
    result_values = Column(JSON, nullable=False)
    reference_ranges = Column(JSON, nullable=True)
    abnormal_flags = Column(JSON, nullable=True)
    interpretative_comments = Column(String, nullable=True)
    
    # Signatures
    is_signed = Column(Boolean, default=False)
    signed_by_id = Column(String, nullable=True)
    signed_by_name = Column(String, nullable=True)
    signed_by_designation = Column(String, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    
    # Status: PENDING_VALIDATION, VALIDATED, PENDING_RELEASE, RELEASED, AMENDED
    status = Column(String, default="PENDING_RELEASE", index=True)
    current_version = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    releases = relationship("ReportRelease", back_populates="report")
    versions = relationship("ReportVersion", back_populates="report")
    audit_logs = relationship("ReportAuditLog", back_populates="report")

class ReportRelease(Base):
    __tablename__ = "lis_report_release"
    id = Column(String, primary_key=True, default=generate_uuid)
    report_id = Column(String, ForeignKey("lis_reports.id"), nullable=False, index=True)
    released_by_id = Column(String, nullable=False)
    released_by_name = Column(String, nullable=False)
    distribution_channels = Column(JSON, nullable=False) # ["portal", "email", "sms"]
    recipients = Column(JSON, nullable=False) # ["patient@email.com", "dr.smith@email.com"]
    released_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("LabReport", back_populates="releases")

class ReportVersion(Base):
    __tablename__ = "lis_report_versions"
    id = Column(String, primary_key=True, default=generate_uuid)
    report_id = Column(String, ForeignKey("lis_reports.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    changes_made = Column(JSON, nullable=False) # diffs
    amended_by_id = Column(String, nullable=False)
    amended_by_name = Column(String, nullable=False)
    amended_at = Column(DateTime, default=datetime.utcnow)
    previous_snapshot = Column(JSON, nullable=False) # full payload of prior state

    report = relationship("LabReport", back_populates="versions")

class ReportAuditLog(Base):
    __tablename__ = "lis_report_audit_logs"
    id = Column(String, primary_key=True, default=generate_uuid)
    report_id = Column(String, ForeignKey("lis_reports.id"), nullable=False, index=True)
    action_type = Column(String, nullable=False) # GENERATED, SIGNED, RELEASED, AMENDED, VIEWED
    actor_id = Column(String, nullable=False)
    actor_name = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    report = relationship("LabReport", back_populates="audit_logs")
