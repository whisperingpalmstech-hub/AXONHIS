import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class TokenQueue(Base):
    __tablename__ = "kiosk_token_queue"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_number = Column(Integer, nullable=False)
    token_prefix = Column(String(10), default="T")
    token_display = Column(String(20), nullable=False) # e.g. T-015
    department = Column(String(100), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), nullable=True)
    patient_uhid = Column(String(50), nullable=True)
    patient_name = Column(String(100), nullable=True)
    status = Column(String(50), default="Pending") # Pending, Calling, In Consultation, Completed, Cancelled, No Show
    priority = Column(Boolean, default=False)
    priority_reason = Column(String(100), nullable=True)
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    called_at = Column(DateTime(timezone=True), nullable=True)
    counter_id = Column(UUID(as_uuid=True), ForeignKey("kiosk_queue_counters.id"), nullable=True)

class TokenHistory(Base):
    __tablename__ = "kiosk_token_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_id = Column(UUID(as_uuid=True), ForeignKey("kiosk_token_queue.id", ondelete="CASCADE"))
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    changed_by = Column(UUID(as_uuid=True), nullable=True)

class QueueCounter(Base):
    __tablename__ = "kiosk_queue_counters"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    counter_name = Column(String(50), nullable=False) # e.g., Counter 3, Room 101
    department = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)

class KioskSession(Base):
    __tablename__ = "kiosk_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kiosk_machine_id = Column(String(50), nullable=False)
    session_start = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    session_end = Column(DateTime(timezone=True), nullable=True)
    action_performed = Column(String(100), nullable=False) # Token Print, New Appointment, Check-In
    patient_uhid = Column(String(50), nullable=True)
    status = Column(String(50), default="Completed")

class AppointmentCheckIn(Base):
    __tablename__ = "kiosk_appointment_checkins"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUID(as_uuid=True), nullable=False)
    patient_uhid = Column(String(50), nullable=True)
    checkin_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    token_id = Column(UUID(as_uuid=True), ForeignKey("kiosk_token_queue.id"))

class QueueAnnouncement(Base):
    __tablename__ = "kiosk_queue_announcements"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_id = Column(UUID(as_uuid=True), ForeignKey("kiosk_token_queue.id"))
    announcement_text = Column(String(255), nullable=False)
    announced_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_successful = Column(Boolean, default=True)
