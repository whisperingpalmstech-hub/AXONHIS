"""
LIS Phlebotomy & Sample Collection Engine – Pydantic Schemas
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


# ── Worklist ──────────────────────────────────────────────────────────────────

class WorklistItemOut(BaseModel):
    id: str
    order_id: str
    order_item_id: str
    order_number: str
    patient_id: str
    patient_name: Optional[str] = None
    patient_uhid: Optional[str] = None
    visit_id: Optional[str] = None
    test_code: str
    test_name: str
    sample_type: str
    barcode: Optional[str] = None
    priority: str
    collection_location: str
    status: str
    consent_required: bool = False
    consent_uploaded: bool = False
    assigned_collector: Optional[str] = None
    scheduled_time: Optional[str] = None
    is_repeat: bool = False
    created_at: Optional[str] = None
    class Config:
        from_attributes = True


class WorklistFilterParams(BaseModel):
    location: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    collector: Optional[str] = None


# ── Patient Verification ──────────────────────────────────────────────────────

class PatientVerificationRequest(BaseModel):
    worklist_id: str
    verification_method: str = Field(default="UHID", description="UHID, MOBILE, ID_CARD, BIOMETRIC")
    verified_by: str


class PatientVerificationResponse(BaseModel):
    verified: bool
    patient_name: str
    patient_uhid: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    photo_url: Optional[str] = None


# ── Sample Collection ─────────────────────────────────────────────────────────

class CollectSampleRequest(BaseModel):
    worklist_id: str
    collector_name: str
    collector_id: Optional[str] = None
    container_type: str = "PLAIN_TUBE"
    collection_location: str = "OPD"
    identity_verified: bool = True
    identity_method: str = "UHID"
    notes: Optional[str] = None
    quantity_ml: Optional[float] = None


class SampleCollectionOut(BaseModel):
    id: str
    worklist_id: str
    sample_id: str
    order_id: str
    patient_id: str
    patient_uhid: Optional[str] = None
    barcode: str
    test_code: str
    test_name: str
    sample_type: str
    container_type: str
    collection_location: str
    collector_name: str
    collected_at: Optional[str] = None
    status: str
    identity_verified: bool
    identity_method: Optional[str] = None
    notes: Optional[str] = None
    quantity_ml: Optional[float] = None
    class Config:
        from_attributes = True


class UpdateSampleStatusRequest(BaseModel):
    status: str
    updated_by: Optional[str] = None
    notes: Optional[str] = None


# ── Consent ───────────────────────────────────────────────────────────────────

class UploadConsentRequest(BaseModel):
    worklist_id: str
    file_name: str
    file_url: str
    file_format: str = "PDF"
    uploaded_by: Optional[str] = None


class ConsentDocumentOut(BaseModel):
    id: str
    worklist_id: str
    patient_id: str
    test_code: str
    document_type: str
    file_name: str
    file_url: str
    file_format: str
    uploaded_by: Optional[str] = None
    uploaded_at: Optional[str] = None
    verified: bool = False
    class Config:
        from_attributes = True


# ── Repeat Schedule ───────────────────────────────────────────────────────────

class CreateRepeatScheduleRequest(BaseModel):
    order_id: str
    patient_id: str
    test_code: str
    test_name: str
    total_samples: int = 3
    interval_minutes: int = 30
    schedule_config: Optional[dict] = None


class RepeatScheduleOut(BaseModel):
    id: str
    order_id: str
    patient_id: str
    test_code: str
    test_name: str
    total_samples: int
    collected_count: int
    interval_minutes: int
    schedule_config: Optional[dict] = None
    is_complete: bool
    started_at: Optional[str] = None
    created_at: Optional[str] = None
    class Config:
        from_attributes = True


# ── Transport ─────────────────────────────────────────────────────────────────

class CreateTransportBatchRequest(BaseModel):
    sample_ids: list[str]
    transport_personnel: str
    transport_method: str = "MANUAL"
    notes: Optional[str] = None


class ReceiveTransportRequest(BaseModel):
    received_by: str


class TransportBatchOut(BaseModel):
    id: str
    batch_id: str
    sample_ids: list | dict
    sample_count: int
    transport_personnel: str
    transport_method: str
    dispatch_time: Optional[str] = None
    received_time: Optional[str] = None
    received_by: Optional[str] = None
    status: str
    notes: Optional[str] = None
    class Config:
        from_attributes = True


# ── Barcode ───────────────────────────────────────────────────────────────────

class BarcodeLabel(BaseModel):
    barcode: str
    sample_id: str
    patient_uhid: Optional[str] = None
    order_number: str
    test_name: str
    sample_type: str
    collected_at: str


# ── Audit ─────────────────────────────────────────────────────────────────────

class AuditEntryOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    performed_by: Optional[str] = None
    details: Optional[dict] = None
    performed_at: Optional[str] = None
    class Config:
        from_attributes = True


# ── Home Collection ───────────────────────────────────────────────────────────

class HomeCollectionRequest(BaseModel):
    patient_id: str
    patient_name: str
    patient_address: str
    patient_phone: str
    test_codes: list[str]
    preferred_time: Optional[str] = None
    notes: Optional[str] = None


class HomeCollectionOut(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    patient_address: str
    status: str
    assigned_phlebotomist: Optional[str] = None
    scheduled_time: Optional[str] = None
    test_details: list[str]
    created_at: Optional[str] = None
