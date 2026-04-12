"""
LIS Laboratory Processing & Result Entry Engine – Pydantic Schemas
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


# ── Processing Worklist ───────────────────────────────────────────────────────

class WorklistOut(BaseModel):
    id: str; cr_receipt_id: Optional[str] = None; sample_id: str; barcode: str
    order_id: str; order_number: str; patient_id: str
    patient_name: Optional[str] = None; patient_uhid: Optional[str] = None
    test_code: str; test_name: str; sample_type: str; department: str
    priority: str; receipt_time: Optional[str] = None
    assigned_technician: Optional[str] = None; status: str
    started_at: Optional[str] = None; completed_at: Optional[str] = None
    created_at: Optional[str] = None
    class Config:
        from_attributes = True


class AssignTechRequest(BaseModel):
    technician: str


class StartProcessingRequest(BaseModel):
    technician: str


# ── Result Entry ──────────────────────────────────────────────────────────────

class EnterResultRequest(BaseModel):
    worklist_id: str
    result_type: str = "NUMERIC"
    result_value: Optional[str] = None
    result_numeric: Optional[float] = None
    result_unit: Optional[str] = None
    result_source: str = "MANUAL"
    analyzer_id: Optional[str] = None
    entered_by: str
    comments: Optional[str] = None


class BatchResultItem(BaseModel):
    worklist_id: str
    result_type: str = "NUMERIC"
    result_value: Optional[str] = None
    result_numeric: Optional[float] = None
    result_unit: Optional[str] = None
    comments: Optional[str] = None


class BatchResultRequest(BaseModel):
    items: list[BatchResultItem]
    result_source: str = "MANUAL"
    entered_by: str


class ResultOut(BaseModel):
    id: str; worklist_id: str; sample_id: str; order_id: str; patient_id: str
    test_code: str; test_name: str; result_type: str
    result_value: Optional[str] = None; result_numeric: Optional[float] = None
    result_unit: Optional[str] = None
    reference_low: Optional[float] = None; reference_high: Optional[float] = None
    result_source: str; analyzer_id: Optional[str] = None
    entered_by: str; entered_at: Optional[str] = None
    is_reviewed: bool; reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None; status: str
    flags: list["FlagOut"] = []
    delta: Optional["DeltaOut"] = None
    comments: list["CommentOut"] = []
    class Config:
        from_attributes = True


class ReviewResultRequest(BaseModel):
    reviewed_by: str
    remarks: Optional[str] = None


class ValidateResultRequest(BaseModel):
    validated_by: str
    remarks: Optional[str] = None


class ReleaseResultRequest(BaseModel):
    released_by: str
    remarks: Optional[str] = None


class RejectResultRequest(BaseModel):
    rejected_by: str
    reason: str


# ── Result Flags ──────────────────────────────────────────────────────────────

class FlagOut(BaseModel):
    id: str; result_id: str; flag_type: str
    reference_low: Optional[float] = None; reference_high: Optional[float] = None
    result_value: Optional[float] = None; is_critical: bool
    message: Optional[str] = None; created_at: Optional[str] = None
    class Config:
        from_attributes = True


# ── Delta Checks ─────────────────────────────────────────────────────────────

class DeltaOut(BaseModel):
    id: str; result_id: str; patient_id: str; test_code: str
    current_value: float; previous_value: float
    previous_date: Optional[str] = None
    delta_absolute: float; delta_percent: float
    threshold_percent: float; is_significant: bool
    message: Optional[str] = None; created_at: Optional[str] = None
    class Config:
        from_attributes = True


# ── QC Results ────────────────────────────────────────────────────────────────

class RecordQCRequest(BaseModel):
    department: str
    test_code: str
    test_name: str
    qc_lot_number: str
    qc_level: str = "NORMAL"
    expected_value: float
    expected_sd: float = 0
    actual_value: float
    analyzer_id: Optional[str] = None
    performed_by: str
    remarks: Optional[str] = None


class QCOut(BaseModel):
    id: str; department: str; test_code: str; test_name: str
    qc_lot_number: str; qc_level: str
    expected_value: float; expected_sd: float; actual_value: float
    status: str; analyzer_id: Optional[str] = None
    performed_by: str; performed_at: Optional[str] = None
    remarks: Optional[str] = None
    class Config:
        from_attributes = True


# ── Comments ──────────────────────────────────────────────────────────────────

class AddCommentRequest(BaseModel):
    result_id: str
    comment_type: str = "REMARK"
    comment_text: str
    added_by: str


class CommentOut(BaseModel):
    id: str; result_id: str; comment_type: str; comment_text: str
    is_template: bool; added_by: str; added_at: Optional[str] = None
    class Config:
        from_attributes = True


# ── Audit ─────────────────────────────────────────────────────────────────────

class AuditOut(BaseModel):
    id: str; entity_type: str; entity_id: str; action: str
    performed_by: Optional[str] = None; details: Optional[dict] = None
    performed_at: Optional[str] = None
    class Config:
        from_attributes = True


# ── Dashboard Stats ───────────────────────────────────────────────────────────

class ProcessingStats(BaseModel):
    total_pending: int = 0
    in_progress: int = 0
    results_entered: int = 0
    awaiting_validation: int = 0
    critical_flags: int = 0
    delta_alerts: int = 0
    qc_failures: int = 0
    department_counts: dict = {}
