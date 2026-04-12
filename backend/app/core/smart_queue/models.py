"""OPD Smart Queue & Flow Orchestration Engine — Database Models"""
import uuid
from datetime import datetime
from enum import StrEnum
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer, Float,
    ForeignKey, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


# ── Enums ────────────────────────────────────────────────────────────────────

class QueueStatus(StrEnum):
    waiting = "waiting"
    called = "called"
    in_consultation = "in_consultation"
    skipped = "skipped"  # Missed patient recovery logic
    completed = "completed"
    transferred = "transferred"
    cancelled = "cancelled"

class RoomStatus(StrEnum):
    open = "open"
    closed = "closed"
    break_time = "break"
    emergency_pause = "emergency_pause"

class QueuePriority(StrEnum):
    emergency = "emergency"
    priority = "priority"
    vip = "vip"
    appointment = "appointment"
    walk_in = "walk_in"

class WayfindingStep(StrEnum):
    lobby = "lobby"
    elevator = "elevator"
    floor = "floor"
    waiting_area = "waiting_area"
    consultation_room = "consultation_room"


# ── 1. Queue Master ─────────────────────────────────────────────────────────

class QueueMaster(Base):
    """Represents a doctor's or department's active queue"""
    __tablename__ = "queue_master"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), nullable=True)
    department = Column(String(100), nullable=True)
    queue_date = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    room_number = Column(String(50), nullable=True)
    room_status = Column(String(30), default=RoomStatus.open)
    status_reason = Column(Text, nullable=True)
    
    max_capacity = Column(Integer, default=50)
    current_length = Column(Integer, default=0)
    avg_consult_time_min = Column(Float, default=15.0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_queue_master_doctor", "doctor_id"),
        Index("ix_queue_master_date", "queue_date"),
    )


# ── 2. Queue Patient Position ───────────────────────────────────────────────

class QueuePatientPosition(Base):
    """The individual patient's position and logic in the queue line"""
    __tablename__ = "queue_patient_position"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    queue_id = Column(UUID(as_uuid=True), ForeignKey("queue_master.id"), nullable=False)
    visit_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    
    status = Column(String(30), default=QueueStatus.waiting)
    priority_level = Column(String(30), default=QueuePriority.walk_in)
    
    # Priority weighting for sort: Emergency=1, Priority=2, VIP=3, Apt=4, WalkIn=5
    calculated_priority_score = Column(Integer, default=5)
    
    position_number = Column(Integer, nullable=True)
    estimated_wait_time_min = Column(Integer, nullable=True)
    estimated_call_time = Column(DateTime(timezone=True), nullable=True)
    
    # Missed Patient Recovery Logic
    missed_calls_count = Column(Integer, default=0)
    last_called_at = Column(DateTime(timezone=True), nullable=True)
    
    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    consultation_started_at = Column(DateTime(timezone=True), nullable=True)
    consultation_ended_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_queue_patient_queue", "queue_id"),
        Index("ix_queue_patient_visit", "visit_id"),
        Index("ix_queue_patient_status", "status"),
    )


# ── 3. Queue Events (Audit Log) ─────────────────────────────────────────────

class QueueEvent(Base):
    """Audit trail for every movement, skip, delay in the queue"""
    __tablename__ = "queue_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    queue_id = Column(UUID(as_uuid=True), ForeignKey("queue_master.id"), nullable=False)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    
    event_type = Column(String(50), nullable=False)
    # joined, called, missed, moved_to_standby, consultation_started, completed, cancelled, manual_override
    
    event_details = Column(JSON, default=dict)
    actor_id = Column(UUID(as_uuid=True), nullable=True) # Who did the override/call
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_queue_events_visit", "visit_id"),
    )


# ── 4. Queue Notifications ──────────────────────────────────────────────────

class QueueNotification(Base):
    """Log of SMS, App Push, or WhatsApp alerts sent to patient"""
    __tablename__ = "queue_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    
    channel = Column(String(30), nullable=False) # sms, whatsapp, push
    notification_type = Column(String(50), nullable=False) # next_in_queue, ready, doctor_delayed
    
    message_content = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    status = Column(String(30), default="sent")


# ── 5. Wayfinding Navigation ────────────────────────────────────────────────

class WayfindingNode(Base):
    """Digital Maps nodes for building wayfinding guide"""
    __tablename__ = "wayfinding_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(String(50), unique=True, nullable=False) # e.g. "lobby_main", "wing_b_fl2"
    node_type = Column(String(50), default=WayfindingStep.floor)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    directions_from_parent = Column(Text, nullable=True)
    parent_node_id = Column(String(50), nullable=True)


class RoomWayfindingMapping(Base):
    """Maps a consultation room to wayfinding instructions"""
    __tablename__ = "queue_room_mapping"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_number = Column(String(50), unique=True, nullable=False)
    department = Column(String(100), nullable=False)
    wayfinding_node_id = Column(String(50), nullable=True)
    display_instructions = Column(Text, nullable=True) # "Proceed to OPD Wing B, Floor 2, Room 203"


# ── 6. OPD Crowd Prediction Engine ──────────────────────────────────────────

class CrowdPredictionSnapshot(Base):
    """AI predictive outputs for hospital crowd lengths"""
    __tablename__ = "queue_wait_time_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_date = Column(DateTime(timezone=True), nullable=False)
    department = Column(String(100), nullable=True)
    
    predicted_peak_start = Column(String(10), nullable=True) # "10:30"
    predicted_peak_end = Column(String(10), nullable=True)   # "13:00"
    predicted_inflow_count = Column(Integer, default=0)
    
    confidence_score = Column(Float, default=0.0)
    factors_used = Column(JSON, default=list) # ["seasonal illness", "holiday"]
    
    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_prediction_date", "prediction_date"),
    )
