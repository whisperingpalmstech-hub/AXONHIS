from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Boolean, Integer, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class ApprovalPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MdApprovalGate(Base):
    """
    Approval gate model for high-risk operations.
    Requires human approval before executing critical operations.
    """
    __tablename__ = "md_approval_gate"

    gate_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gate_name = Column(String(255), nullable=False)
    gate_code = Column(String(100), unique=True, nullable=False, index=True)
    gate_type = Column(String(50), nullable=False)  # MEDICATION_ORDER, LAB_ORDER, DIAGNOSIS, etc.
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=True)
    approval_criteria = Column(JSONB, nullable=False, default={})  # Conditions requiring approval
    required_roles = Column(JSONB, nullable=False, default=[])  # Roles that can approve
    auto_approve_after_minutes = Column(Integer, nullable=True)  # Auto-approve after timeout
    notify_approvers = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("md_facility.facility_id"), nullable=True)
    specialty_profile_id = Column(UUID(as_uuid=True), ForeignKey("md_specialty_profile.specialty_profile_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class MdApprovalRequest(Base):
    """
    Approval request model for tracking approval workflows.
    """
    __tablename__ = "md_approval_request"

    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gate_id = Column(UUID(as_uuid=True), ForeignKey("md_approval_gate.gate_id", ondelete="CASCADE"), nullable=False, index=True)
    request_type = Column(String(50), nullable=False, index=True)
    request_data = Column(JSONB, nullable=False, default={})  # The data requiring approval
    requester_id = Column(UUID(as_uuid=True), nullable=False)  # User who initiated the request
    requester_name = Column(String(255), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("md_patient.patient_id", ondelete="CASCADE"), nullable=True, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=True, index=True)
    priority = Column(String(20), default=ApprovalPriority.MEDIUM, nullable=False)
    status = Column(String(30), default=ApprovalStatus.PENDING, nullable=False, index=True)
    urgency_reason = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    approved_by = Column(String(100), nullable=True)
    rejected_by = Column(String(100), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    gate = relationship("MdApprovalGate", backref="requests")
    patient = relationship("MdPatient", backref="approval_requests")
    encounter = relationship("MdEncounter", backref="approval_requests")

    __table_args__ = (
        Index('idx_approval_request_status_priority', 'status', 'priority'),
        Index('idx_approval_request_patient', 'patient_id', 'created_at'),
    )


class MdApprovalAction(Base):
    """
    Approval action model for tracking individual approval actions.
    """
    __tablename__ = "md_approval_action"

    action_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("md_approval_request.request_id", ondelete="CASCADE"), nullable=False, index=True)
    approver_id = Column(UUID(as_uuid=True), nullable=False)
    approver_name = Column(String(255), nullable=False)
    approver_role = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)  # APPROVE, REJECT, COMMENT
    comments = Column(Text, nullable=True)
    action_data = Column(JSONB, nullable=False, default={})  # Additional action metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    request = relationship("MdApprovalRequest", backref="actions")

    __table_args__ = (
        Index('idx_approval_action_request', 'request_id', 'created_at'),
    )
