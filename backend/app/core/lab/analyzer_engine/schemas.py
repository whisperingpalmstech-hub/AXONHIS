"""
LIS Analyzer & Device Integration Engine – Pydantic Schemas
"""
from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel


# ── Device ────────────────────────────────────────────────────────────────────

class DeviceCreate(BaseModel):
    device_code: str
    device_name: str
    device_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    department: str
    protocol: str = "HL7"
    connection_string: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    test_code_mappings: Optional[dict] = None
    result_format_config: Optional[dict] = None


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    status: Optional[str] = None
    protocol: Optional[str] = None
    connection_string: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    test_code_mappings: Optional[dict] = None
    result_format_config: Optional[dict] = None
    is_active: Optional[bool] = None


class DeviceOut(BaseModel):
    id: str; device_code: str; device_name: str; device_type: str
    manufacturer: Optional[str] = None; model: Optional[str] = None
    serial_number: Optional[str] = None; department: str
    protocol: str; connection_string: Optional[str] = None
    ip_address: Optional[str] = None; port: Optional[int] = None
    status: str; last_communication: Optional[str] = None
    last_maintenance: Optional[str] = None
    test_code_mappings: Optional[dict] = None
    result_format_config: Optional[dict] = None
    is_active: bool; created_at: Optional[str] = None
    class Config:
        from_attributes = True


# ── Worklist ──────────────────────────────────────────────────────────────────

class WorklistSendRequest(BaseModel):
    device_id: str
    sample_id: str; barcode: str
    patient_id: str; patient_uhid: Optional[str] = None; patient_name: Optional[str] = None
    order_id: str; test_code: str; test_name: str
    priority: str = "ROUTINE"


class BatchWorklistRequest(BaseModel):
    device_id: str
    items: list[WorklistSendRequest]


class AnalyzerWorklistOut(BaseModel):
    id: str; device_id: str; sample_id: str; barcode: str
    patient_id: str; patient_uhid: Optional[str] = None; patient_name: Optional[str] = None
    order_id: str; test_code: str; test_name: str
    analyzer_test_code: Optional[str] = None; priority: str; status: str
    sent_at: Optional[str] = None; acknowledged_at: Optional[str] = None
    completed_at: Optional[str] = None; created_at: Optional[str] = None
    class Config:
        from_attributes = True


# ── Analyzer Results ──────────────────────────────────────────────────────────

class AnalyzerResultReceive(BaseModel):
    device_id: str
    sample_id: str; barcode: Optional[str] = None
    test_code: str; analyzer_test_code: Optional[str] = None
    result_value: Optional[str] = None; result_numeric: Optional[float] = None
    result_unit: Optional[str] = None; result_flag: Optional[str] = None
    raw_message: Optional[str] = None; is_qc_sample: bool = False


class BatchResultReceive(BaseModel):
    device_id: str
    results: list[AnalyzerResultReceive]


class VerifyResultRequest(BaseModel):
    verified_by: str


class AnalyzerResultOut(BaseModel):
    id: str; device_id: str; worklist_id: Optional[str] = None
    sample_id: str; barcode: Optional[str] = None
    patient_id: Optional[str] = None; test_code: str
    analyzer_test_code: Optional[str] = None
    result_value: Optional[str] = None; result_numeric: Optional[float] = None
    result_unit: Optional[str] = None; result_flag: Optional[str] = None
    status: str; match_confidence: Optional[float] = None
    is_qc_sample: bool; verified_by: Optional[str] = None
    verified_at: Optional[str] = None; received_at: Optional[str] = None
    imported_at: Optional[str] = None
    class Config:
        from_attributes = True


# ── Reagent Usage ─────────────────────────────────────────────────────────────

class RecordReagentRequest(BaseModel):
    device_id: str; reagent_name: str; reagent_lot: Optional[str] = None
    test_code: str; quantity_used: float = 1.0; unit: str = "tests"
    current_stock: Optional[float] = None; reorder_level: Optional[float] = None


class ReagentUsageOut(BaseModel):
    id: str; device_id: str; reagent_name: str; reagent_lot: Optional[str] = None
    test_code: str; quantity_used: float; unit: str
    current_stock: Optional[float] = None; reorder_level: Optional[float] = None
    is_low_stock: bool; recorded_at: Optional[str] = None
    class Config:
        from_attributes = True


# ── Device Errors ─────────────────────────────────────────────────────────────

class ReportErrorRequest(BaseModel):
    device_id: str; error_code: Optional[str] = None
    error_type: str; severity: str = "ERROR"
    message: str; raw_data: Optional[str] = None


class ResolveErrorRequest(BaseModel):
    resolved_by: str


class DeviceErrorOut(BaseModel):
    id: str; device_id: str; error_code: Optional[str] = None
    error_type: str; severity: str; message: str
    raw_data: Optional[str] = None; is_resolved: bool
    resolved_by: Optional[str] = None; resolved_at: Optional[str] = None
    occurred_at: Optional[str] = None
    class Config:
        from_attributes = True


# ── Audit ─────────────────────────────────────────────────────────────────────

class DeviceAuditOut(BaseModel):
    id: str; device_id: str; action: str; direction: str
    data_transmitted: Optional[str] = None; data_received: Optional[str] = None
    status: str; error_message: Optional[str] = None
    performed_by: Optional[str] = None; details: Optional[dict] = None
    performed_at: Optional[str] = None
    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────────

class AnalyzerDashboardStats(BaseModel):
    total_devices: int = 0
    online_devices: int = 0
    offline_devices: int = 0
    maintenance_devices: int = 0
    error_devices: int = 0
    pending_worklists: int = 0
    unverified_results: int = 0
    unresolved_errors: int = 0
    low_stock_reagents: int = 0
    department_status: dict = {}
    results_today: int = 0
