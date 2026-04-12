from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class WebhookStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class WebhookEventType(str, Enum):
    ENCOUNTER_CREATED = "ENCOUNTER_CREATED"
    ENCOUNTER_UPDATED = "ENCOUNTER_UPDATED"
    PATIENT_CREATED = "PATIENT_CREATED"
    PATIENT_UPDATED = "PATIENT_UPDATED"
    DIAGNOSIS_ADDED = "DIAGNOSIS_ADDED"
    MEDICATION_ORDERED = "MEDICATION_ORDERED"
    LAB_RESULT_READY = "LAB_RESULT_READY"
    DOCUMENT_GENERATED = "DOCUMENT_GENERATED"
    CUSTOM = "CUSTOM"


class WebhookSubscriptionCreate(BaseModel):
    subscription_name: str
    subscriber_name: str
    webhook_url: str
    secret_key: Optional[str] = None
    event_types: List[WebhookEventType]
    headers: dict = Field(default_factory=dict)
    retry_policy: dict = Field(default_factory=dict)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    verify_ssl: bool = True
    filter_rules: dict = Field(default_factory=dict)
    rate_limit_per_minute: int = Field(default=60, ge=1)
    created_by: str


class WebhookSubscriptionUpdate(BaseModel):
    subscription_name: Optional[str] = None
    webhook_url: Optional[str] = None
    secret_key: Optional[str] = None
    event_types: Optional[List[WebhookEventType]] = None
    headers: Optional[dict] = None
    retry_policy: Optional[dict] = None
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    verify_ssl: Optional[bool] = None
    filter_rules: Optional[dict] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1)
    status: Optional[WebhookStatus] = None


class WebhookSubscriptionResponse(BaseModel):
    subscription_id: UUID
    subscription_name: str
    subscriber_name: str
    webhook_url: str
    secret_key: Optional[str]
    event_types: List[str]
    headers: dict
    status: WebhookStatus
    retry_policy: dict
    timeout_seconds: int
    verify_ssl: bool
    filter_rules: dict
    rate_limit_per_minute: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime]

    class Config:
        from_attributes = True


class WebhookDeliveryResponse(BaseModel):
    delivery_id: UUID
    subscription_id: UUID
    event_type: str
    event_id: Optional[UUID]
    payload: dict
    status: str
    http_status_code: Optional[int]
    response_body: Optional[str]
    attempt_count: int
    max_attempts: int
    next_retry_at: Optional[datetime]
    error_message: Optional[str]
    delivered_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookEventPayload(BaseModel):
    event_type: str
    event_id: Optional[UUID] = None
    timestamp: datetime
    data: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
