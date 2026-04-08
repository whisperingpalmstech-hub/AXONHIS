from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class RuleStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"


class RuleSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ALERT = "ALERT"
    CRITICAL = "CRITICAL"


class RuleTriggerType(str, Enum):
    ON_ENCOUNTER_CREATE = "ON_ENCOUNTER_CREATE"
    ON_ENCOUNTER_UPDATE = "ON_ENCOUNTER_UPDATE"
    ON_DIAGNOSIS_ADD = "ON_DIAGNOSIS_ADD"
    ON_MEDICATION_ORDER = "ON_MEDICATION_ORDER"
    ON_LAB_ORDER = "ON_LAB_ORDER"
    ON_LAB_RESULT = "ON_LAB_RESULT"
    ON_VITALS_UPDATE = "ON_VITALS_UPDATE"
    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"


class ClinicalRuleCreate(BaseModel):
    rule_code: str
    rule_name: str
    rule_description: Optional[str] = None
    rule_category: str
    rule_version: str = "1.0"
    status: RuleStatus = RuleStatus.DRAFT
    severity: RuleSeverity = RuleSeverity.INFO
    trigger_type: RuleTriggerType
    condition_expression: dict = Field(default_factory=dict)
    action_config: dict = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    specialty_profile_id: Optional[UUID] = None
    facility_id: Optional[UUID] = None
    requires_approval: bool = False
    auto_execute: bool = False
    created_by: str
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class ClinicalRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    rule_description: Optional[str] = None
    rule_category: Optional[str] = None
    status: Optional[RuleStatus] = None
    severity: Optional[RuleSeverity] = None
    condition_expression: Optional[dict] = None
    action_config: Optional[dict] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    requires_approval: Optional[bool] = None
    auto_execute: Optional[bool] = None
    updated_by: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class ClinicalRuleResponse(BaseModel):
    rule_id: UUID
    rule_code: str
    rule_name: str
    rule_description: Optional[str]
    rule_category: str
    rule_version: str
    status: RuleStatus
    severity: RuleSeverity
    trigger_type: RuleTriggerType
    condition_expression: dict
    action_config: dict
    priority: int
    specialty_profile_id: Optional[UUID]
    facility_id: Optional[UUID]
    requires_approval: bool
    auto_execute: bool
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    effective_from: Optional[datetime]
    effective_to: Optional[datetime]

    class Config:
        from_attributes = True


class RuleExecutionCreate(BaseModel):
    rule_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    trigger_event: str
    trigger_data: dict = Field(default_factory=dict)


class RuleExecutionResponse(BaseModel):
    execution_id: UUID
    rule_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID]
    trigger_event: str
    trigger_data: dict
    execution_status: str
    rule_matched: bool
    action_taken: dict
    error_message: Optional[str]
    execution_time_ms: Optional[float]
    executed_at: datetime

    class Config:
        from_attributes = True


class RuleAlertResponse(BaseModel):
    alert_id: UUID
    execution_id: UUID
    rule_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID]
    alert_title: str
    alert_message: str
    severity: str
    alert_type: str
    suggested_action: Optional[str]
    action_required: bool
    acknowledged: bool
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    dismissed: bool
    dismissed_by: Optional[str]
    dismissed_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class RuleEvaluationContext(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    trigger_event: str
    trigger_data: dict = Field(default_factory=dict)
    additional_context: dict = Field(default_factory=dict)


class RuleEvaluationResult(BaseModel):
    rule_id: UUID
    rule_matched: bool
    actions: List[dict] = Field(default_factory=list)
    alerts: List[dict] = Field(default_factory=list)


class RuleSearchQuery(BaseModel):
    rule_category: Optional[str] = None
    status: Optional[RuleStatus] = None
    severity: Optional[RuleSeverity] = None
    trigger_type: Optional[RuleTriggerType] = None
    specialty_profile_id: Optional[UUID] = None
    facility_id: Optional[UUID] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class RuleSearchResponse(BaseModel):
    rules: List[ClinicalRuleResponse]
    total_count: int
    has_more: bool
