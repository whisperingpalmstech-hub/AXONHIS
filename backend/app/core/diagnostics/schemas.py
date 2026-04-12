from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class DiagnosticTemplateBase(BaseModel):
    procedure_name: str
    department: str
    structured_fields_schema: Dict[str, Any]
    rich_text_layout: Optional[str] = None
    is_active: bool = True

class DiagnosticTemplateCreate(DiagnosticTemplateBase):
    pass

class DiagnosticTemplateOut(DiagnosticTemplateBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DiagnosticProcedureOrderBase(BaseModel):
    patient_id: str
    uhid: str
    encounter_id: Optional[str] = None
    encounter_type: str
    template_id: str
    ordering_doctor_id: str
    clinical_notes: Optional[str] = None
    priority: str = "ROUTINE"

class DiagnosticProcedureOrderCreate(DiagnosticProcedureOrderBase):
    pass

class DiagnosticProcedureOrderOut(DiagnosticProcedureOrderBase):
    id: str
    status: str
    billing_reference: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DiagnosticWorkbenchRecordOut(BaseModel):
    id: str
    order_id: str
    assigned_technician_id: Optional[str] = None
    assigned_doctor_id: Optional[str] = None
    workflow_state: str
    scheduled_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    order: DiagnosticProcedureOrderOut
    model_config = ConfigDict(from_attributes=True)

class DiagnosticResultEntryCreate(BaseModel):
    technician_id: str
    structured_data: Dict[str, Any]
    findings_richtext: Optional[str] = None
    impression: Optional[str] = None

class DiagnosticResultEntryOut(DiagnosticResultEntryCreate):
    id: str
    workbench_id: str
    provisional_release_time: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DiagnosticValidationCreate(BaseModel):
    doctor_id: str
    action: str # APPROVED, REJECTED_FOR_REDO
    modified_structured_data: Optional[Dict[str, Any]] = None
    modified_findings: Optional[str] = None
    modified_impression: Optional[str] = None
    comments: Optional[str] = None

class DiagnosticValidationOut(DiagnosticValidationCreate):
    id: str
    workbench_id: str
    digital_signature_hash: Optional[str] = None
    validated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DiagnosticReportOut(BaseModel):
    id: str
    validation_id: str
    pdf_file_path: str
    qr_code_hash: str
    is_latest: bool
    generated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DiagnosticReportHandoverCreate(BaseModel):
    delivery_method: str
    recipient: Optional[str] = None
    handled_by: str

class DiagnosticReportHandoverOut(DiagnosticReportHandoverCreate):
    id: str
    workbench_id: str
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class DiagnosticAmendmentLogCreate(BaseModel):
    amending_doctor_id: str
    reason: str

class DiagnosticAmendmentLogOut(DiagnosticAmendmentLogCreate):
    id: str
    workbench_id: str
    previous_report_id: str
    amended_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DiagnosticDashboardMetrics(BaseModel):
    pending_procedures: int
    procedures_in_progress: int
    awaiting_validation: int
    completed_reports: int
    average_tat_minutes: float
