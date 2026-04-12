import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class DiagnosticTemplate(Base):
    __tablename__ = "diagnostic_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    procedure_name = Column(String, nullable=False, unique=True, index=True) # e.g., '2D ECHO', 'ECG'
    department = Column(String, nullable=False) # e.g., 'Cardiology'
    structured_fields_schema = Column(JSON, nullable=False, default=dict)
    rich_text_layout = Column(Text, nullable=True) # HTML template string
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DiagnosticProcedureOrder(Base):
    __tablename__ = "diagnostic_procedure_orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, index=True, nullable=False)
    uhid = Column(String, index=True, nullable=False)
    encounter_id = Column(String, index=True, nullable=True) # visit_id or admission_number
    encounter_type = Column(String, nullable=False) # 'OPD', 'IPD', 'ER'
    template_id = Column(String, ForeignKey("diagnostic_templates.id"), nullable=False)
    
    ordering_doctor_id = Column(String, nullable=False)
    clinical_notes = Column(Text, nullable=True)
    priority = Column(String, default="ROUTINE") # ROUTINE, URGENT, STAT
    status = Column(String, default="ORDERED") # ORDERED, BILLED, CANCELLED
    billing_reference = Column(String, nullable=True) # Bill number
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    template = relationship("DiagnosticTemplate")
    workbench_record = relationship("DiagnosticWorkbenchRecord", back_populates="order", uselist=False)

class DiagnosticWorkbenchRecord(Base):
    __tablename__ = "diagnostic_workbench_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, ForeignKey("diagnostic_procedure_orders.id"), unique=True, nullable=False)
    
    assigned_technician_id = Column(String, nullable=True)
    assigned_doctor_id = Column(String, nullable=True)
    
    # States: PENDING_ACCEPTANCE, IN_PROGRESS, PROVISIONALLY_RELEASED, VALIDATED, FINALIZED, AMENDED, CANCELLED
    workflow_state = Column(String, default="PENDING_ACCEPTANCE", index=True)
    
    scheduled_time = Column(DateTime, nullable=True)
    start_time = Column(DateTime, nullable=True)
    completion_time = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    order = relationship("DiagnosticProcedureOrder", back_populates="workbench_record")
    result_entry = relationship("DiagnosticResultEntry", back_populates="workbench", uselist=False)
    validations = relationship("DiagnosticValidation", back_populates="workbench")
    handover = relationship("DiagnosticReportHandover", back_populates="workbench", uselist=False)
    amendments = relationship("DiagnosticAmendmentLog", back_populates="workbench")

class DiagnosticResultEntry(Base):
    __tablename__ = "diagnostic_result_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workbench_id = Column(String, ForeignKey("diagnostic_workbench_records.id"), unique=True, nullable=False)
    
    technician_id = Column(String, nullable=False)
    structured_data = Column(JSON, nullable=False, default=dict)
    findings_richtext = Column(Text, nullable=True)
    impression = Column(Text, nullable=True)
    
    provisional_release_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    workbench = relationship("DiagnosticWorkbenchRecord", back_populates="result_entry")

class DiagnosticValidation(Base):
    __tablename__ = "diagnostic_validations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workbench_id = Column(String, ForeignKey("diagnostic_workbench_records.id"), nullable=False)
    doctor_id = Column(String, nullable=False)
    
    # For doctor modifying technician's findings
    modified_structured_data = Column(JSON, nullable=True)
    modified_findings = Column(Text, nullable=True)
    modified_impression = Column(Text, nullable=True)
    
    action = Column(String, nullable=False) # 'APPROVED', 'REJECTED_FOR_REDO'
    comments = Column(Text, nullable=True)
    digital_signature_hash = Column(String, nullable=True)
    
    validated_at = Column(DateTime, default=datetime.utcnow)
    
    workbench = relationship("DiagnosticWorkbenchRecord", back_populates="validations")
    report = relationship("DiagnosticReport", back_populates="validation", uselist=False)

class DiagnosticReport(Base):
    __tablename__ = "diagnostic_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    validation_id = Column(String, ForeignKey("diagnostic_validations.id"), unique=True, nullable=False)
    
    pdf_file_path = Column(String, nullable=False)
    qr_code_hash = Column(String, nullable=False, unique=True)
    is_latest = Column(Boolean, default=True) # False if amended
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    validation = relationship("DiagnosticValidation", back_populates="report")

class DiagnosticReportHandover(Base):
    __tablename__ = "diagnostic_report_handovers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workbench_id = Column(String, ForeignKey("diagnostic_workbench_records.id"), nullable=False)
    
    delivery_method = Column(String, nullable=False) # 'PRINT_WITH_HEADER', 'PRINT_WITHOUT_HEADER', 'EMAIL', 'PORTAL'
    recipient = Column(String, nullable=True) # Email addr or physical recipient
    handled_by = Column(String, nullable=False) # Staff ID
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    workbench = relationship("DiagnosticWorkbenchRecord", back_populates="handover")

class DiagnosticAmendmentLog(Base):
    __tablename__ = "diagnostic_amendment_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workbench_id = Column(String, ForeignKey("diagnostic_workbench_records.id"), nullable=False)
    amending_doctor_id = Column(String, nullable=False)
    
    reason = Column(Text, nullable=False)
    previous_report_id = Column(String, ForeignKey("diagnostic_reports.id"), nullable=False)
    
    amended_at = Column(DateTime, default=datetime.utcnow)
    
    workbench = relationship("DiagnosticWorkbenchRecord", back_populates="amendments")
