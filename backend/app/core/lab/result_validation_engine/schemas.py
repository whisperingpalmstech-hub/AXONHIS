from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ValidationRecordOut(BaseModel):
    id: str
    worklist_id: str
    stage_name: str
    validator_name: str
    action: str
    corrections_made: Optional[Dict[str, Any]] = None
    remarks: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class ValidationFlagOut(BaseModel):
    id: str
    flag_type: str
    reference_range: Optional[str] = None
    recorded_value: Optional[str] = None
    alert_message: Optional[str] = None
    notified_to: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ValidationRejectionOut(BaseModel):
    id: str
    worklist_id: str
    rejected_by_name: str
    rejection_reason: str
    action_taken: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class ValidationWorklistOut(BaseModel):
    id: str
    sample_id: str
    patient_name: str
    patient_uhid: str
    test_order_id: str
    test_code: str
    test_name: str
    department: str
    result_value: Optional[str] = None
    result_unit: Optional[str] = None
    priority_level: str
    validation_stage: str
    is_critical_alert: bool
    analyzer_device_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    records: List[ValidationRecordOut] = []
    flags: List[ValidationFlagOut] = []
    rejections: List[ValidationRejectionOut] = []

    class Config:
        from_attributes = True

class ApproveResultRequest(BaseModel):
    validator_id: str
    validator_name: str
    stage_name: str # e.g., "Technician", "Senior Technician", "Pathologist"
    remarks: Optional[str] = None

class CorrectResultRequest(BaseModel):
    validator_id: str
    validator_name: str
    stage_name: str
    new_value: str
    remarks: Optional[str] = None

class RejectResultRequest(BaseModel):
    validator_id: str
    validator_name: str
    rejection_reason: str
    action_taken: str # e.g., "SEND_FOR_RETEST"

class BatchApproveRequest(BaseModel):
    worklist_ids: List[str]
    validator_id: str
    validator_name: str
    stage_name: str

class ValidationAuditOut(BaseModel):
    id: str
    worklist_id: str
    action_type: str
    actor_name: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class ValidationPerformanceOut(BaseModel):
    total_validated: int
    total_rejected: int
    critical_alerts: int
    avg_turnaround_time_mins: float
    workload_distribution: Dict[str, int]
