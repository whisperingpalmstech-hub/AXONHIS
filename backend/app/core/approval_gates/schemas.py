from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class ApprovalPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalGateCreate(BaseModel):
    gate_name: str
    gate_code: str
    gate_type: str
    risk_level: str
    description: Optional[str] = None
    approval_criteria: dict = Field(default_factory=dict)
    required_roles: List[str] = Field(default_factory=list)
    auto_approve_after_minutes: Optional[int] = None
    notify_approvers: bool = True
    facility_id: Optional[UUID] = None
    specialty_profile_id: Optional[UUID] = None


class ApprovalGateResponse(BaseModel):
    gate_id: UUID
    gate_name: str
    gate_code: str
    gate_type: str
    risk_level: str
    description: Optional[str]
    approval_criteria: dict
    required_roles: List[str]
    auto_approve_after_minutes: Optional[int]
    notify_approvers: bool
    is_active: bool
    facility_id: Optional[UUID]
    specialty_profile_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApprovalRequestCreate(BaseModel):
    gate_id: UUID
    request_type: str
    request_data: dict = Field(default_factory=dict)
    requester_id: UUID
    requester_name: str
    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    priority: ApprovalPriority = ApprovalPriority.MEDIUM
    urgency_reason: Optional[str] = None
    expires_after_minutes: Optional[int] = None


class ApprovalRequestResponse(BaseModel):
    request_id: UUID
    gate_id: UUID
    request_type: str
    request_data: dict
    requester_id: UUID
    requester_name: str
    patient_id: Optional[UUID]
    encounter_id: Optional[UUID]
    priority: str
    status: ApprovalStatus
    urgency_reason: Optional[str]
    expires_at: Optional[datetime]
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]
    approved_by: Optional[str]
    rejected_by: Optional[str]
    rejection_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalActionCreate(BaseModel):
    approver_id: UUID
    approver_name: str
    approver_role: str
    action: str
    comments: Optional[str] = None
    action_data: dict = Field(default_factory=dict)


class ApprovalActionResponse(BaseModel):
    action_id: UUID
    request_id: UUID
    approver_id: UUID
    approver_name: str
    approver_role: str
    action: str
    comments: Optional[str]
    action_data: dict
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalCheckResult(BaseModel):
    requires_approval: bool
    gate_id: Optional[UUID] = None
    gate_name: Optional[str] = None
    reason: Optional[str] = None
