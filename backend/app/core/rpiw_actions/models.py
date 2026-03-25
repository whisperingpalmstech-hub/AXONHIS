import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class RpiwAction(Base):
    """Central registry of all clinical actions initiated from the unified Workspace."""
    __tablename__ = "rpiw_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_uhid = Column(String, nullable=False, index=True)
    admission_number = Column(String, nullable=True, index=True)
    visit_id = Column(String, nullable=True, index=True)
    
    action_type = Column(String, nullable=False)  # note, order, prescription, task
    status = Column(String, default="Initiated")  # Initiated, Validated, Routed, Completed, Failed
    created_by_user_id = Column(String, nullable=False)
    created_by_role = Column(String, nullable=False)
    
    validation_status = Column(String, default="Pending") # Pending, Passed, Failed
    validation_remarks = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    executed_at = Column(DateTime(timezone=True), nullable=True)


class RpiwClinicalNote(Base):
    """Structured clinical notes taking."""
    __tablename__ = "rpiw_clinical_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_id = Column(UUID(as_uuid=True), ForeignKey("rpiw_actions.id", ondelete="CASCADE"), nullable=False, index=True)
    note_type = Column(String, nullable=False)  # Progress, Nursing, Procedure, Discharge
    content = Column(Text, nullable=False)
    is_signed = Column(Boolean, default=False)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RpiwOrder(Base):
    """Orders for clinical services (Labs, Radiology)."""
    __tablename__ = "rpiw_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_id = Column(UUID(as_uuid=True), ForeignKey("rpiw_actions.id", ondelete="CASCADE"), nullable=False, index=True)
    order_category = Column(String, nullable=False)  # laboratory, radiology, procedure, consult
    item_code = Column(String, nullable=False)
    item_name = Column(String, nullable=False)
    priority = Column(String, default="Routine")
    routed_to_module = Column(String, nullable=True)  # LIS, RIS
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RpiwPrescription(Base):
    """Medication prescriptions from the workspace."""
    __tablename__ = "rpiw_prescriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_id = Column(UUID(as_uuid=True), ForeignKey("rpiw_actions.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    route = Column(String, nullable=False)
    duration_days = Column(Integer, nullable=False)
    instructions = Column(String, nullable=True)
    routed_to_pharmacy = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RpiwTask(Base):
    """Task assignments for clinical staff."""
    __tablename__ = "rpiw_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_id = Column(UUID(as_uuid=True), ForeignKey("rpiw_actions.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_role = Column(String, nullable=False)  # e.g., nurse, phlebotomist
    assigned_user_id = Column(String, nullable=True)
    task_description = Column(String, nullable=False)
    priority = Column(String, default="Routine")
    due_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="Assigned") # Assigned, In Progress, Completed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RpiwActionLog(Base):
    """Immutable audit trail of actions."""
    __tablename__ = "rpiw_action_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_id = Column(UUID(as_uuid=True), ForeignKey("rpiw_actions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False)  # Created, Validated, Routed, Executed, Failed
    event_details = Column(JSONB, nullable=True)
    user_id = Column(String, nullable=False)
    role_code = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
