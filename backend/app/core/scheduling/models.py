"""
Enterprise Scheduling – Database Models
========================================
Tables:
  - doctor_calendars        : Doctor availability calendar with recurring patterns
  - calendar_slots          : Individual time slots (available/booked/blocked/overbooked)
  - slot_bookings           : Slot-level booking records linking patient → slot
  - overbooking_configs     : Per-doctor / per-department overbooking rules
  - cyclic_schedules        : Recurring weekly schedule templates
  - modality_resources      : MRI / CT / XRay / Ultrasound machines
  - modality_slots          : Time slots for modality equipment
  - appointment_reminders   : SMS / email / WhatsApp reminders
  - follow_up_rules         : Automated follow-up scheduling rules
  - scheduling_analytics    : Pre-computed analytics snapshots
"""

import uuid
from datetime import datetime, date, time, timezone, timedelta
from enum import StrEnum

from sqlalchemy import (
    Column, String, DateTime, Date, Time, Integer, Float, Boolean,
    ForeignKey, Text, JSON, CheckConstraint, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


# ─────────────────────────── Enums ───────────────────────────────────────────

class SlotStatus(StrEnum):
    AVAILABLE = "available"
    BOOKED = "booked"
    BLOCKED = "blocked"
    OVERBOOKED = "overbooked"


class AppointmentType(StrEnum):
    IN_PERSON = "in_person"
    TELECONSULTATION = "teleconsultation"
    EMERGENCY = "emergency"
    FOLLOW_UP = "follow_up"


class ModalityType(StrEnum):
    MRI = "mri"
    CT = "ct"
    XRAY = "xray"
    ULTRASOUND = "ultrasound"


class ReminderChannel(StrEnum):
    SMS = "sms"
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class ReminderStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class DayOfWeek(StrEnum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


# ───────────────────── 1. Doctor Calendar ────────────────────────────────────

class DoctorCalendar(Base):
    """Master calendar record for each doctor."""
    __tablename__ = "doctor_calendars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    department = Column(String(100), nullable=False, index=True)
    default_slot_duration_min = Column(Integer, default=15, nullable=False)
    max_patients_per_slot = Column(Integer, default=1, nullable=False)
    allow_teleconsultation = Column(Boolean, default=True, nullable=False)
    allow_overbooking = Column(Boolean, default=False, nullable=False)
    max_overbook_count = Column(Integer, default=2, nullable=False)
    buffer_between_slots_min = Column(Integer, default=5, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    doctor = relationship("User", foreign_keys=[doctor_id], backref="doctor_calendar")
    slots = relationship("CalendarSlot", back_populates="calendar", cascade="all, delete-orphan")
    cyclic_schedules = relationship("CyclicSchedule", back_populates="calendar", cascade="all, delete-orphan")


# ───────────────────── 2. Calendar Slots ─────────────────────────────────────

class CalendarSlot(Base):
    """Individual time slot for a doctor's calendar."""
    __tablename__ = "calendar_slots"
    __table_args__ = (
        Index("ix_calslot_doctor_date", "doctor_id", "slot_date"),
        Index("ix_calslot_status", "status"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    calendar_id = Column(UUID(as_uuid=True), ForeignKey("doctor_calendars.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    slot_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(String(20), default=SlotStatus.AVAILABLE, nullable=False)
    appointment_type = Column(String(30), default=AppointmentType.IN_PERSON, nullable=False)
    current_bookings = Column(Integer, default=0, nullable=False)
    max_bookings = Column(Integer, default=1, nullable=False)
    is_emergency_override = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    calendar = relationship("DoctorCalendar", back_populates="slots")
    bookings = relationship("SlotBooking", back_populates="slot", cascade="all, delete-orphan")


# ───────────────────── 3. Slot Bookings ──────────────────────────────────────

class SlotBooking(Base):
    """Links a patient to a specific slot – the actual appointment record."""
    __tablename__ = "slot_bookings"
    __table_args__ = (
        Index("ix_slotbook_patient", "patient_id"),
        Index("ix_slotbook_doctor_date", "doctor_id", "booking_date"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slot_id = Column(UUID(as_uuid=True), ForeignKey("calendar_slots.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    department = Column(String(100), nullable=False)
    booking_date = Column(Date, nullable=False)
    appointment_type = Column(String(30), default=AppointmentType.IN_PERSON, nullable=False)
    status = Column(String(30), default="confirmed", nullable=False)  # confirmed, checked_in, completed, cancelled, no_show
    reason = Column(Text, nullable=True)
    qr_code_data = Column(Text, nullable=True)  # QR appointment slip
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    completion_time = Column(DateTime(timezone=True), nullable=True)
    is_follow_up = Column(Boolean, default=False, nullable=False)
    parent_booking_id = Column(UUID(as_uuid=True), ForeignKey("slot_bookings.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    slot = relationship("CalendarSlot", back_populates="bookings")
    patient = relationship("Patient", backref=__import__('sqlalchemy.orm', fromlist=['backref']).backref("slot_bookings", cascade="all, delete-orphan"))
    doctor = relationship("User", foreign_keys=[doctor_id], backref="slot_bookings_as_doctor")
    reminders = relationship("AppointmentReminder", back_populates="booking", cascade="all, delete-orphan")


# ───────────────────── 4. Overbooking Config ────────────────────────────────

class OverbookingConfig(Base):
    """Per-doctor or per-department overbooking rules."""
    __tablename__ = "overbooking_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    department = Column(String(100), nullable=True, index=True)
    max_overbook_per_slot = Column(Integer, default=2, nullable=False)
    max_overbook_per_day = Column(Integer, default=10, nullable=False)
    priority_threshold = Column(Integer, default=3, nullable=False)  # 1-5,  ≥ threshold allows overbook
    allow_emergency_override = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ───────────────────── 5. Cyclic Schedule ────────────────────────────────────

class CyclicSchedule(Base):
    """Recurring weekly schedule template – generates slots automatically."""
    __tablename__ = "cyclic_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    calendar_id = Column(UUID(as_uuid=True), ForeignKey("doctor_calendars.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(String(3), nullable=False)  # mon, tue, wed, thu, fri, sat, sun
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration_min = Column(Integer, default=15, nullable=False)
    appointment_type = Column(String(30), default=AppointmentType.IN_PERSON, nullable=False)
    max_patients_per_slot = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date, nullable=True)  # null = indefinite

    calendar = relationship("DoctorCalendar", back_populates="cyclic_schedules")


# ───────────────────── 6. Modality Resources ─────────────────────────────────

class ModalityResource(Base):
    """Equipment / machine for imaging modalities (MRI, CT, XRay, Ultrasound)."""
    __tablename__ = "modality_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    modality_type = Column(String(20), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    location = Column(String(200), nullable=True)
    department = Column(String(100), default="Radiology", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    max_slots_per_day = Column(Integer, default=40, nullable=False)
    slot_duration_min = Column(Integer, default=30, nullable=False)
    buffer_min = Column(Integer, default=10, nullable=False)
    operating_start = Column(Time, nullable=False, default=time(8, 0))
    operating_end = Column(Time, nullable=False, default=time(20, 0))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    slots = relationship("ModalitySlot", back_populates="resource", cascade="all, delete-orphan")


# ───────────────────── 7. Modality Slots ─────────────────────────────────────

class ModalitySlot(Base):
    """Time slot for a specific modality machine."""
    __tablename__ = "modality_slots"
    __table_args__ = (
        Index("ix_modslot_resource_date", "resource_id", "slot_date"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("modality_resources.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    slot_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(String(20), default=SlotStatus.AVAILABLE, nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    imaging_order_id = Column(UUID(as_uuid=True), nullable=True)  # link to RIS
    technician_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    resource = relationship("ModalityResource", back_populates="slots")


# ───────────────────── 8. Appointment Reminders ──────────────────────────────

class AppointmentReminder(Base):
    """Scheduled reminders for appointments (24h, 2h, etc.)."""
    __tablename__ = "appointment_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("slot_bookings.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    channel = Column(String(20), nullable=False)  # sms, email, whatsapp
    recipient = Column(String(200), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default=ReminderStatus.PENDING, nullable=False)
    reminder_type = Column(String(30), default="24h_before", nullable=False)  # 24h_before, 2h_before, follow_up
    message_template = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    booking = relationship("SlotBooking", back_populates="reminders")


# ───────────────────── 9. Follow-Up Rules ────────────────────────────────────

class FollowUpRule(Base):
    """Rules for automated follow-up scheduling."""
    __tablename__ = "follow_up_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department = Column(String(100), nullable=False, index=True)
    diagnosis_code = Column(String(20), nullable=True)  # ICD code
    follow_up_days = Column(Integer, nullable=False, default=7)
    follow_up_type = Column(String(30), default=AppointmentType.FOLLOW_UP, nullable=False)
    auto_schedule = Column(Boolean, default=True, nullable=False)
    reminder_before_days = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ───────────────────── 10. Scheduling Analytics ──────────────────────────────

class SchedulingAnalytics(Base):
    """Pre-computed daily analytics snapshots."""
    __tablename__ = "scheduling_analytics"
    __table_args__ = (
        UniqueConstraint("analytics_date", "doctor_id", name="uq_analytics_date_doctor"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analytics_date = Column(Date, nullable=False, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    department = Column(String(100), nullable=True)

    # Slot metrics
    total_slots = Column(Integer, default=0)
    booked_slots = Column(Integer, default=0)
    available_slots = Column(Integer, default=0)
    blocked_slots = Column(Integer, default=0)
    overbooked_slots = Column(Integer, default=0)

    # Appointment metrics
    total_appointments = Column(Integer, default=0)
    completed_appointments = Column(Integer, default=0)
    cancelled_appointments = Column(Integer, default=0)
    no_show_count = Column(Integer, default=0)

    # Utilization
    slot_utilization_pct = Column(Float, default=0.0)
    doctor_utilization_pct = Column(Float, default=0.0)
    no_show_rate_pct = Column(Float, default=0.0)
    avg_wait_time_min = Column(Float, nullable=True)

    # Modality (optional)
    modality_type = Column(String(20), nullable=True)

    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
