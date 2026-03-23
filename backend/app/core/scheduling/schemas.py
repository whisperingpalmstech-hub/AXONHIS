"""
Enterprise Scheduling – Pydantic Schemas
"""

import uuid
from datetime import datetime, date, time
from pydantic import BaseModel, Field


# ─────────────────────── Doctor Calendar ─────────────────────────────────────

class DoctorCalendarCreate(BaseModel):
    doctor_id: uuid.UUID
    department: str = Field(min_length=1, max_length=100)
    default_slot_duration_min: int = 15
    max_patients_per_slot: int = 1
    allow_teleconsultation: bool = True
    allow_overbooking: bool = False
    max_overbook_count: int = 2
    buffer_between_slots_min: int = 5


class DoctorCalendarUpdate(BaseModel):
    default_slot_duration_min: int | None = None
    max_patients_per_slot: int | None = None
    allow_teleconsultation: bool | None = None
    allow_overbooking: bool | None = None
    max_overbook_count: int | None = None
    buffer_between_slots_min: int | None = None
    is_active: bool | None = None


class DoctorCalendarOut(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    department: str
    default_slot_duration_min: int
    max_patients_per_slot: int
    allow_teleconsultation: bool
    allow_overbooking: bool
    max_overbook_count: int
    buffer_between_slots_min: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────── Calendar Slots ──────────────────────────────────────

class SlotCreate(BaseModel):
    calendar_id: uuid.UUID
    doctor_id: uuid.UUID
    slot_date: date
    start_time: time
    end_time: time
    appointment_type: str = "in_person"
    max_bookings: int = 1
    notes: str | None = None


class SlotBulkGenerate(BaseModel):
    """Generate slots for a date range from cyclic schedule."""
    calendar_id: uuid.UUID
    doctor_id: uuid.UUID
    start_date: date
    end_date: date


class SlotOut(BaseModel):
    id: uuid.UUID
    calendar_id: uuid.UUID
    doctor_id: uuid.UUID
    slot_date: date
    start_time: time
    end_time: time
    status: str
    appointment_type: str
    current_bookings: int
    max_bookings: int
    is_emergency_override: bool
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SlotStatusUpdate(BaseModel):
    status: str  # available, blocked
    notes: str | None = None


# ─────────────────────── Slot Bookings ───────────────────────────────────────

class BookingCreate(BaseModel):
    slot_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    department: str = Field(min_length=1)
    appointment_type: str = "in_person"
    reason: str | None = None
    is_follow_up: bool = False
    parent_booking_id: uuid.UUID | None = None


class BookingUpdate(BaseModel):
    status: str | None = None
    reason: str | None = None


class BookingOut(BaseModel):
    id: uuid.UUID
    slot_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    department: str
    booking_date: date
    appointment_type: str
    status: str
    reason: str | None
    qr_code_data: str | None
    check_in_time: datetime | None
    completion_time: datetime | None
    is_follow_up: bool
    parent_booking_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmergencyOverrideRequest(BaseModel):
    doctor_id: uuid.UUID
    patient_id: uuid.UUID
    department: str
    slot_date: date
    preferred_time: time | None = None
    reason: str


# ─────────────────────── Overbooking Config ──────────────────────────────────

class OverbookingConfigCreate(BaseModel):
    doctor_id: uuid.UUID | None = None
    department: str | None = None
    max_overbook_per_slot: int = 2
    max_overbook_per_day: int = 10
    priority_threshold: int = 3
    allow_emergency_override: bool = True


class OverbookingConfigOut(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID | None
    department: str | None
    max_overbook_per_slot: int
    max_overbook_per_day: int
    priority_threshold: int
    allow_emergency_override: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────── Cyclic Schedule ─────────────────────────────────────

class CyclicScheduleCreate(BaseModel):
    calendar_id: uuid.UUID
    doctor_id: uuid.UUID
    day_of_week: str  # mon, tue, etc.
    start_time: time
    end_time: time
    slot_duration_min: int = 15
    appointment_type: str = "in_person"
    max_patients_per_slot: int = 1
    effective_from: date
    effective_until: date | None = None


class CyclicScheduleOut(BaseModel):
    id: uuid.UUID
    calendar_id: uuid.UUID
    doctor_id: uuid.UUID
    day_of_week: str
    start_time: time
    end_time: time
    slot_duration_min: int
    appointment_type: str
    max_patients_per_slot: int
    is_active: bool
    effective_from: date
    effective_until: date | None

    model_config = {"from_attributes": True}


# ─────────────────────── Modality Resources / Slots ──────────────────────────

class ModalityResourceCreate(BaseModel):
    modality_type: str  # mri, ct, xray, ultrasound
    name: str = Field(min_length=1, max_length=150)
    location: str | None = None
    department: str = "Radiology"
    max_slots_per_day: int = 40
    slot_duration_min: int = 30
    buffer_min: int = 10
    operating_start: time = time(8, 0)
    operating_end: time = time(20, 0)


class ModalityResourceOut(BaseModel):
    id: uuid.UUID
    modality_type: str
    name: str
    location: str | None
    department: str
    is_active: bool
    max_slots_per_day: int
    slot_duration_min: int
    buffer_min: int
    operating_start: time
    operating_end: time
    created_at: datetime

    model_config = {"from_attributes": True}


class ModalitySlotOut(BaseModel):
    id: uuid.UUID
    resource_id: uuid.UUID
    slot_date: date
    start_time: time
    end_time: time
    status: str
    patient_id: uuid.UUID | None
    imaging_order_id: uuid.UUID | None
    technician_id: uuid.UUID | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ModalitySlotBook(BaseModel):
    resource_id: uuid.UUID
    slot_date: date
    start_time: time
    patient_id: uuid.UUID
    imaging_order_id: uuid.UUID | None = None
    technician_id: uuid.UUID | None = None
    notes: str | None = None


class ModalitySlotGenerate(BaseModel):
    resource_id: uuid.UUID
    start_date: date
    end_date: date


# ─────────────────────── Reminders ───────────────────────────────────────────

class ReminderCreate(BaseModel):
    booking_id: uuid.UUID
    channel: str = "sms"
    recipient: str
    reminder_type: str = "24h_before"


class ReminderOut(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    channel: str
    recipient: str
    scheduled_at: datetime
    sent_at: datetime | None
    status: str
    reminder_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────── Follow-Up Rules ─────────────────────────────────────

class FollowUpRuleCreate(BaseModel):
    department: str
    diagnosis_code: str | None = None
    follow_up_days: int = 7
    follow_up_type: str = "follow_up"
    auto_schedule: bool = True
    reminder_before_days: int = 1


class FollowUpRuleOut(BaseModel):
    id: uuid.UUID
    department: str
    diagnosis_code: str | None
    follow_up_days: int
    follow_up_type: str
    auto_schedule: bool
    reminder_before_days: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────── Analytics ───────────────────────────────────────────

class SchedulingAnalyticsOut(BaseModel):
    id: uuid.UUID
    analytics_date: date
    doctor_id: uuid.UUID | None
    department: str | None
    total_slots: int
    booked_slots: int
    available_slots: int
    blocked_slots: int
    overbooked_slots: int
    total_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    no_show_count: int
    slot_utilization_pct: float
    doctor_utilization_pct: float
    no_show_rate_pct: float
    avg_wait_time_min: float | None
    modality_type: str | None
    computed_at: datetime

    model_config = {"from_attributes": True}


class AnalyticsSummary(BaseModel):
    """Aggregated analytics for dashboard."""
    period_start: date
    period_end: date
    total_appointments: int
    completed: int
    cancelled: int
    no_shows: int
    no_show_rate_pct: float
    avg_slot_utilization_pct: float
    avg_doctor_utilization_pct: float
    doctors_with_overload: list[dict] = []
    modality_utilization: list[dict] = []
