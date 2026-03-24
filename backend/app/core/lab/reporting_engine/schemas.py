from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ReportReleaseOut(BaseModel):
    id: str
    report_id: str
    released_by_name: str
    distribution_channels: List[str]
    recipients: List[str]
    released_at: datetime

    class Config:
        from_attributes = True

class ReportVersionOut(BaseModel):
    id: str
    report_id: str
    version_number: int
    changes_made: Dict[str, Any]
    amended_by_name: str
    amended_at: datetime
    previous_snapshot: Dict[str, Any]

    class Config:
        from_attributes = True

class ReportAuditLogOut(BaseModel):
    id: str
    report_id: str
    action_type: str
    actor_name: str
    details: Optional[Dict[str, Any]]
    timestamp: datetime

    class Config:
        from_attributes = True

class LabReportOut(BaseModel):
    id: str
    sample_id: str
    test_order_id: str
    patient_uhid: str
    patient_name: str
    visit_id: Optional[str]
    department: Optional[str]
    
    test_details: Dict[str, Any]
    result_values: Dict[str, Any]
    reference_ranges: Optional[Dict[str, Any]]
    abnormal_flags: Optional[Dict[str, Any]]
    interpretative_comments: Optional[str]
    
    is_signed: bool
    signed_by_name: Optional[str]
    signed_by_designation: Optional[str]
    signed_at: Optional[datetime]
    
    status: str
    current_version: int
    created_at: datetime
    updated_at: datetime

    releases: List[ReportReleaseOut] = []
    versions: List[ReportVersionOut] = []
    audit_logs: List[ReportAuditLogOut] = []

    class Config:
        from_attributes = True

class SignReportRequest(BaseModel):
    signer_id: str
    signer_name: str
    signer_designation: str # Senior Technician, Pathologist, HOD

class ReleaseReportRequest(BaseModel):
    releaser_id: str
    releaser_name: str
    channels: List[str] = ["portal", "email"]
    recipients: List[str]

class BulkReleaseRequest(BaseModel):
    report_ids: List[str]
    releaser_id: str
    releaser_name: str
    channels: List[str] = ["portal", "email"]

class AmendReportRequest(BaseModel):
    amender_id: str
    amender_name: str
    changes_made: Dict[str, Any]
    reason: str
    new_result_values: Dict[str, Any]
    new_comments: Optional[str]
