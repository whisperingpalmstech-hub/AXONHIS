"""Lab module – Pydantic schemas for request/response validation."""
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# ── Lab Test Catalog ─────────────────────────────────────────────────────────

class LabTestCreate(BaseModel):
    code: str
    name: str
    category: str
    sample_type: str = "blood"
    unit: str | None = None
    normal_range_low: float | None = None
    normal_range_high: float | None = None
    reference_range: str | None = None
    critical_low: float | None = None
    critical_high: float | None = None
    price: float = 0
    turnaround_hours: int | None = 24
    is_calculated: bool = False
    calculation_formula: str | None = None


class LabTestOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    category: str
    sample_type: str
    unit: str | None
    normal_range_low: float | None
    normal_range_high: float | None
    reference_range: str | None
    critical_low: float | None
    critical_high: float | None
    price: float
    is_active: bool
    turnaround_hours: int | None
    is_calculated: bool
    calculation_formula: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Lab Order ────────────────────────────────────────────────────────────────

class LabOrderCreate(BaseModel):
    order_id: uuid.UUID
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
    notes: str | None = None


class LabOrderOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
    status: str
    ordered_at: datetime
    completed_at: datetime | None
    notes: str | None

    model_config = ConfigDict(from_attributes=True)


# ── Lab Sample ───────────────────────────────────────────────────────────────

class LabSampleCreate(BaseModel):
    lab_order_id: uuid.UUID
    sample_type: str = "blood"
    notes: str | None = None


class LabSampleOut(BaseModel):
    id: uuid.UUID
    lab_order_id: uuid.UUID
    sample_barcode: str
    sample_type: str
    status: str
    collected_by: uuid.UUID | None
    collection_time: datetime
    received_at: datetime | None
    is_outsourced: bool
    outsourced_to: str | None
    outsourced_date: datetime | None
    notes: str | None

    model_config = ConfigDict(from_attributes=True)


# ── Lab Result ───────────────────────────────────────────────────────────────

class LabResultCreate(BaseModel):
    sample_id: uuid.UUID
    test_id: uuid.UUID
    order_id: uuid.UUID
    patient_id: uuid.UUID
    value: str
    numeric_value: float | None = None
    unit: str | None = None
    reference_range: str | None = None
    notes: str | None = None


class LabResultOut(BaseModel):
    id: uuid.UUID
    sample_id: uuid.UUID
    test_id: uuid.UUID
    order_id: uuid.UUID
    patient_id: uuid.UUID
    value: str
    numeric_value: float | None
    unit: str | None
    reference_range: str | None
    result_flag: str
    is_abnormal: bool
    is_critical: bool
    status: str
    notes: str | None
    entered_by: uuid.UUID | None
    entered_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Lab Validation ───────────────────────────────────────────────────────────

class LabValidationCreate(BaseModel):
    result_id: uuid.UUID
    validation_status: str  # VALIDATED or REJECTED
    rejection_reason: str | None = None


class LabValidationOut(BaseModel):
    id: uuid.UUID
    result_id: uuid.UUID
    validated_by: uuid.UUID | None
    validated_at: datetime | None
    validation_status: str
    rejection_reason: str | None

    model_config = ConfigDict(from_attributes=True)


# ── Lab Processing ───────────────────────────────────────────────────────────

class LabProcessingOut(BaseModel):
    id: uuid.UUID
    sample_id: uuid.UUID
    analyzer_name: str | None
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    notes: str | None

    model_config = ConfigDict(from_attributes=True)


# ── Dashboard Stats ──────────────────────────────────────────────────────────

class LabDashboardStats(BaseModel):
    pending_samples: int
    processing_samples: int
    completed_today: int
    critical_results: int
    pending_validation: int
    total_tests_catalog: int
