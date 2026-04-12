from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class ValidationWorklist(Base):
    __tablename__ = "lis_validation_worklist"
    id = Column(String, primary_key=True, default=generate_uuid)
    sample_id = Column(String, index=True, nullable=False)
    patient_name = Column(String, nullable=False)
    patient_uhid = Column(String, index=True, nullable=False)
    test_order_id = Column(String, index=True, nullable=False)
    test_code = Column(String, nullable=False)
    test_name = Column(String, nullable=False)
    department = Column(String, index=True, nullable=False)
    result_value = Column(String, nullable=True)
    result_unit = Column(String, nullable=True)
    
    # Validation Priority System (Red, Orange, Yellow, Green)
    priority_level = Column(String, default="GREEN", index=True) # CRITICAL (Red), URGENT (Orange), ABNORMAL (Yellow), NORMAL (Green)
    
    # Stage: PENDING_TECH, PENDING_SENIOR, PENDING_PATHOLOGIST, APPROVED, REJECTED
    validation_stage = Column(String, default="PENDING_TECH", index=True)
    
    is_critical_alert = Column(Boolean, default=False)
    analyzer_device_id = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    records = relationship("ValidationRecord", back_populates="worklist")
    flags = relationship("ValidationFlag", back_populates="worklist")
    rejections = relationship("ValidationRejection", back_populates="worklist")

class ValidationRecord(Base):
    __tablename__ = "lis_validation_records"
    id = Column(String, primary_key=True, default=generate_uuid)
    worklist_id = Column(String, ForeignKey("lis_validation_worklist.id"), nullable=False, index=True)
    stage_name = Column(String, nullable=False) # Technician, Senior, Pathologist
    validator_id = Column(String, nullable=False)
    validator_name = Column(String, nullable=False)
    action = Column(String, nullable=False) # APPROVED, REJECTED, CORRECTED
    corrections_made = Column(JSON, nullable=True) # {"old_value": "4.5", "new_value": "4.6"}
    remarks = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    worklist = relationship("ValidationWorklist", back_populates="records")

class ValidationFlag(Base):
    __tablename__ = "lis_validation_flags"
    id = Column(String, primary_key=True, default=generate_uuid)
    worklist_id = Column(String, ForeignKey("lis_validation_worklist.id"), nullable=False, index=True)
    flag_type = Column(String, nullable=False) # HIGH, LOW, CRITICAL
    reference_range = Column(String, nullable=True)
    recorded_value = Column(String, nullable=True)
    alert_message = Column(String, nullable=True)
    notified_to = Column(JSON, nullable=True) # List of staff/doctors notified
    created_at = Column(DateTime, default=datetime.utcnow)

    worklist = relationship("ValidationWorklist", back_populates="flags")

class ValidationRejection(Base):
    __tablename__ = "lis_validation_rejections"
    id = Column(String, primary_key=True, default=generate_uuid)
    worklist_id = Column(String, ForeignKey("lis_validation_worklist.id"), nullable=False, index=True)
    rejected_by_id = Column(String, nullable=False)
    rejected_by_name = Column(String, nullable=False)
    rejection_reason = Column(String, nullable=False)
    action_taken = Column(String, nullable=True) # E.g., SENT_FOR_RETEST
    timestamp = Column(DateTime, default=datetime.utcnow)

    worklist = relationship("ValidationWorklist", back_populates="rejections")

class ValidationAudit(Base):
    __tablename__ = "lis_validation_audit"
    id = Column(String, primary_key=True, default=generate_uuid)
    worklist_id = Column(String, nullable=False, index=True)
    action_type = Column(String, nullable=False) # STAGE_ADVANCED, RESULT_CORRECTED, FLAG_TRIGGERED, REJECTED
    actor_id = Column(String, nullable=False)
    actor_name = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
