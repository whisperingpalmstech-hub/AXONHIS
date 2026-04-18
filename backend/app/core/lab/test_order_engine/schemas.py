"""
LIS Test Order Management Engine – Pydantic Schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal


# ── Test Order Item Schemas ───────────────────────────────────────────────────

class TestOrderItemCreate(BaseModel):
    test_code: str
    test_name: str
    sample_type: str = "BLOOD"
    priority: str = "ROUTINE"
    price: Decimal = Decimal("0.00")
    panel_id: Optional[UUID] = None
    collection_location: Optional[str] = None
    notes: Optional[str] = None


class TestOrderItemOut(BaseModel):
    id: UUID
    order_id: UUID
    test_code: str
    test_name: str
    sample_type: str
    priority: str
    price: Decimal
    status: str
    barcode: Optional[str] = None
    panel_id: Optional[UUID] = None
    collection_location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Test Order Master Schemas ─────────────────────────────────────────────────

class TestOrderCreate(BaseModel):
    patient_id: UUID
    visit_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    ordering_doctor: Optional[str] = None
    department_source: str = "OPD_BILLING"
    order_source: str = "OPD_BILLING"
    priority: str = "ROUTINE"
    clinical_indication: Optional[str] = None
    provisional_diagnosis: Optional[str] = None
    symptoms: Optional[str] = None
    medication_history: Optional[str] = None
    items: List[TestOrderItemCreate] = []


class TestOrderOut(BaseModel):
    id: UUID
    order_number: str
    patient_id: UUID
    visit_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    ordering_doctor: Optional[str] = None
    department_source: str
    order_source: str
    priority: str
    status: str
    clinical_indication: Optional[str] = None
    provisional_diagnosis: Optional[str] = None
    insurance_validated: bool
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    items: List[TestOrderItemOut] = []

    class Config:
        from_attributes = True


# ── Panel Schemas ─────────────────────────────────────────────────────────────

class PanelItemCreate(BaseModel):
    test_code: str
    test_name: str
    sample_type: str = "BLOOD"
    price: Decimal = Decimal("0.00")


class PanelCreate(BaseModel):
    panel_code: str
    panel_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    total_price: Decimal = Decimal("0.00")
    items: List[PanelItemCreate] = []


class PanelItemOut(BaseModel):
    id: UUID
    test_code: str
    test_name: str
    sample_type: str
    price: Decimal

    class Config:
        from_attributes = True


class PanelOut(BaseModel):
    id: UUID
    panel_code: str
    panel_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    total_price: Decimal
    is_active: bool
    panel_items: List[PanelItemOut] = []

    class Config:
        from_attributes = True


# ── Barcode Schema ────────────────────────────────────────────────────────────

class BarcodeOut(BaseModel):
    id: UUID
    barcode: str
    order_id: UUID
    order_item_id: UUID
    patient_id: UUID
    sample_type: str
    collection_time: Optional[datetime] = None
    is_collected: bool

    class Config:
        from_attributes = True


# ── Prescription Scan Schema ─────────────────────────────────────────────────

class PrescriptionScanResult(BaseModel):
    detected_tests: List[str] = []
    ocr_text: str = ""
    confidence: float = 0.0


# ── Phlebotomy Worklist Schema ───────────────────────────────────────────────

class PhlebotomyWorklistItem(BaseModel):
    order_id: UUID
    order_number: str
    patient_id: UUID
    patient_name: Optional[str] = None
    patient_uhid: Optional[str] = None
    test_name: str
    test_code: str
    sample_type: str
    priority: str
    collection_location: Optional[str] = None
    barcode: Optional[str] = None


# ── Audit Trail Schema ───────────────────────────────────────────────────────

class AuditTrailOut(BaseModel):
    id: UUID
    order_id: UUID
    action: str
    performed_by: Optional[UUID] = None
    details: Optional[Dict[str, Any]] = None
    performed_at: datetime

    class Config:
        from_attributes = True


# ── Add Items to existing order ───────────────────────────────────────────────

class AddItemsRequest(BaseModel):
    items: List[TestOrderItemCreate]


class AddPanelRequest(BaseModel):
    panel_id: UUID


# ── Cancel Order ──────────────────────────────────────────────────────────────

class CancelOrderRequest(BaseModel):
    reason: str
