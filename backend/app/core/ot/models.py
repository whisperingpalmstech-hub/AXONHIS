"""
Operating Theatre (OT) Module — Models
========================================
Full surgical workflow: scheduling, anesthesia, intra-op, post-op.
Interconnected with: IPD admissions, billing (ChargePosting), pharmacy (consumables), lab (pre-op tests).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class OTRoom(Base):
    __tablename__ = "ot_rooms"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    room_code = Column(String(50), nullable=False)
    room_name = Column(String(255), nullable=False)
    room_type = Column(String(50), default="general")
    floor = Column(String(50), nullable=True)
    is_laminar_flow = Column(Boolean, default=False)
    has_c_arm = Column(Boolean, default=False)
    has_laser = Column(Boolean, default=False)
    status = Column(String(30), default="available")
    is_active = Column(Boolean, default=True)


class OTSchedule(Base):
    __tablename__ = "ot_schedules"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    ot_room_id = Column(UUID(as_uuid=True), ForeignKey("ot_rooms.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    patient_name = Column(String(255), nullable=False)
    patient_uhid = Column(String(50), nullable=True)
    admission_id = Column(UUID(as_uuid=True), nullable=True)
    encounter_id = Column(UUID(as_uuid=True), nullable=True)
    surgery_name = Column(String(500), nullable=False)
    surgery_code = Column(String(50), nullable=True)
    surgery_type = Column(String(50), default="elective")
    laterality = Column(String(20), nullable=True)
    estimated_duration_mins = Column(Integer, default=60)
    anesthesia_type = Column(String(50), nullable=True)
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    primary_surgeon_id = Column(UUID(as_uuid=True), nullable=False)
    primary_surgeon_name = Column(String(255), nullable=False)
    assistant_surgeons = Column(JSONB, nullable=True)
    anesthesiologist_name = Column(String(255), nullable=True)
    scrub_nurse_name = Column(String(255), nullable=True)
    pre_op_diagnosis = Column(Text, nullable=True)
    consent_obtained = Column(Boolean, default=False)
    pre_op_checklist = Column(JSONB, nullable=True)
    blood_group = Column(String(10), nullable=True)
    blood_units_reserved = Column(Integer, default=0)
    status = Column(String(30), default="scheduled")
    cancellation_reason = Column(Text, nullable=True)
    post_op_diagnosis = Column(Text, nullable=True)
    post_op_notes = Column(Text, nullable=True)
    complications = Column(JSONB, nullable=True)
    specimens = Column(JSONB, nullable=True)
    implants_used = Column(JSONB, nullable=True)
    blood_loss_ml = Column(Integer, nullable=True)
    total_charges = Column(Numeric(14, 2), default=0)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True)


class OTConsumable(Base):
    __tablename__ = "ot_consumables"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False)
    ot_schedule_id = Column(UUID(as_uuid=True), ForeignKey("ot_schedules.id"), nullable=False)
    item_name = Column(String(255), nullable=False)
    item_code = Column(String(50), nullable=True)
    item_id = Column(UUID(as_uuid=True), nullable=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(12, 2), default=0)
    total_price = Column(Numeric(12, 2), default=0)
    category = Column(String(50), nullable=True)
    is_returned = Column(Boolean, default=False)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class OTAnesthesiaRecord(Base):
    __tablename__ = "ot_anesthesia_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False)
    ot_schedule_id = Column(UUID(as_uuid=True), ForeignKey("ot_schedules.id"), nullable=False)
    anesthesia_type = Column(String(50), nullable=False)
    asa_score = Column(String(10), nullable=True)
    airway = Column(String(50), nullable=True)
    induction_time = Column(DateTime(timezone=True), nullable=True)
    extubation_time = Column(DateTime(timezone=True), nullable=True)
    medications_given = Column(JSONB, nullable=True)
    vital_signs_log = Column(JSONB, nullable=True)
    complications = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    recorded_by = Column(UUID(as_uuid=True), nullable=False)
    recorded_by_name = Column(String(255), nullable=True)
