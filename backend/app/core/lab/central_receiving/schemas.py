"""
LIS Central Receiving & Specimen Tracking Engine – Pydantic Schemas
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Receipt ───────────────────────────────────────────────────────────────────

class RegisterSampleRequest(BaseModel):
    barcode: str
    received_by: str
    notes: Optional[str] = None


class ReceiptOut(BaseModel):
    id: str
    sample_id: str
    barcode: str
    order_id: str
    order_number: str
    patient_id: str
    patient_name: Optional[str] = None
    patient_uhid: Optional[str] = None
    test_code: str
    test_name: str
    sample_type: str
    container_type: Optional[str] = None
    collection_time: Optional[str] = None
    collection_location: Optional[str] = None
    priority: str
    transport_batch_id: Optional[str] = None
    received_by: str
    received_at: Optional[str] = None
    status: str
    current_location: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ── Verification ──────────────────────────────────────────────────────────────

class VerifySampleRequest(BaseModel):
    receipt_id: str
    sample_type_correct: bool = True
    container_correct: bool = True
    volume_adequate: bool = True
    labeling_correct: bool = True
    transport_ok: bool = True
    hemolyzed: bool = False
    clotted: bool = False
    verified_by: str
    remarks: Optional[str] = None


class VerificationOut(BaseModel):
    id: str
    receipt_id: str
    sample_type_correct: bool
    container_correct: bool
    volume_adequate: bool
    labeling_correct: bool
    transport_ok: bool
    hemolyzed: bool
    clotted: bool
    overall_result: str
    verified_by: str
    verified_at: Optional[str] = None
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


# ── Rejection ─────────────────────────────────────────────────────────────────

class RejectSampleRequest(BaseModel):
    receipt_id: str
    rejection_reason: str
    rejection_details: Optional[str] = None
    rejected_by: str
    recollection_requested: bool = True


class RejectionOut(BaseModel):
    id: str
    receipt_id: str
    rejection_reason: str
    rejection_details: Optional[str] = None
    rejected_by: str
    rejected_at: Optional[str] = None
    recollection_requested: bool
    notification_sent: bool
    notification_targets: Optional[dict] = None

    class Config:
        from_attributes = True


# ── Routing ───────────────────────────────────────────────────────────────────

class RouteSampleRequest(BaseModel):
    receipt_id: str
    target_department: Optional[str] = None  # auto-detected if None
    routed_by: str
    notes: Optional[str] = None


class ReceiveAtDeptRequest(BaseModel):
    received_by_dept: str


class RoutingOut(BaseModel):
    id: str
    receipt_id: str
    target_department: str
    routed_by: str
    routed_at: Optional[str] = None
    received_at_dept: Optional[str] = None
    received_by_dept: Optional[str] = None
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ── Storage ───────────────────────────────────────────────────────────────────

class StoreSampleRequest(BaseModel):
    receipt_id: str
    storage_location: str
    storage_temperature: str = "2-8°C"
    max_duration_hours: int = 24
    stored_by: str


class RetrieveSampleRequest(BaseModel):
    retrieved_by: str


class StorageOut(BaseModel):
    id: str
    receipt_id: str
    storage_location: str
    storage_temperature: str
    max_duration_hours: int
    stored_at: Optional[str] = None
    stored_by: str
    retrieved_at: Optional[str] = None
    retrieved_by: Optional[str] = None
    is_active: bool
    alert_sent: bool

    class Config:
        from_attributes = True


# ── Chain of Custody ──────────────────────────────────────────────────────────

class CustodyEntryOut(BaseModel):
    id: str
    receipt_id: str
    sample_id: str
    stage: str
    location: str
    responsible_staff: str
    timestamp: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# ── Alerts ────────────────────────────────────────────────────────────────────

class AlertOut(BaseModel):
    id: str
    alert_type: str
    severity: str
    sample_id: Optional[str] = None
    order_number: Optional[str] = None
    patient_name: Optional[str] = None
    message: str
    status: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class AcknowledgeAlertRequest(BaseModel):
    acknowledged_by: str


# ── Audit ─────────────────────────────────────────────────────────────────────

class CRAuditOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    performed_by: Optional[str] = None
    details: Optional[dict] = None
    performed_at: Optional[str] = None

    class Config:
        from_attributes = True


# ── Dashboard Stats ───────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    received_today: int = 0
    pending_verification: int = 0
    accepted: int = 0
    rejected: int = 0
    routed: int = 0
    stored: int = 0
    active_alerts: int = 0
    department_distribution: dict = {}
