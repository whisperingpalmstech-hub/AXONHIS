from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class EventStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class EventType(str, Enum):
    ENCOUNTER_CREATED = "ENCOUNTER_CREATED"
    ENCOUNTER_UPDATED = "ENCOUNTER_UPDATED"
    ENCOUNTER_CLOSED = "ENCOUNTER_CLOSED"
    PATIENT_CREATED = "PATIENT_CREATED"
    PATIENT_UPDATED = "PATIENT_UPDATED"
    DIAGNOSIS_CREATED = "DIAGNOSIS_CREATED"
    MEDICATION_ORDERED = "MEDICATION_ORDERED"
    LAB_ORDERED = "LAB_ORDERED"
    LAB_RESULT = "LAB_RESULT"
    DOCUMENT_CREATED = "DOCUMENT_CREATED"
    SHARE_GRANTED = "SHARE_GRANTED"
    BILLING_INVOICE_CREATED = "BILLING_INVOICE_CREATED"
    APPOINTMENT_BOOKED = "APPOINTMENT_BOOKED"
    APPOINTMENT_CANCELLED = "APPOINTMENT_CANCELLED"
    CUSTOM = "CUSTOM"


class EventCreate(BaseModel):
    event_type: str
    event_name: str
    event_version: str = "1.0"
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    source_system: str
    source_type: str
    aggregate_id: Optional[UUID] = None
    aggregate_type: Optional[str] = None
    payload: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    expires_at: Optional[datetime] = None


class EventResponse(BaseModel):
    event_id: UUID
    event_type: str
    event_name: str
    event_version: str
    correlation_id: Optional[str]
    causation_id: Optional[str]
    source_system: str
    source_type: str
    aggregate_id: Optional[UUID]
    aggregate_type: Optional[str]
    payload: dict
    metadata: dict
    status: EventStatus
    retry_count: int
    max_retries: int
    error_message: Optional[str]
    processed_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class EventSubscriptionCreate(BaseModel):
    subscriber_name: str
    subscriber_type: str  # webhook, service, queue
    event_types: List[str]
    endpoint_url: Optional[str] = None
    queue_name: Optional[str] = None
    service_name: Optional[str] = None
    filter_rules: dict = Field(default_factory=dict)
    retry_policy: dict = Field(default_factory=dict)


class EventSubscriptionUpdate(BaseModel):
    event_types: Optional[List[str]] = None
    endpoint_url: Optional[str] = None
    queue_name: Optional[str] = None
    service_name: Optional[str] = None
    filter_rules: Optional[dict] = None
    retry_policy: Optional[dict] = None
    active_flag: Optional[bool] = None


class EventSubscriptionResponse(BaseModel):
    subscription_id: UUID
    subscriber_name: str
    subscriber_type: str
    event_types: List[str]
    endpoint_url: Optional[str]
    queue_name: Optional[str]
    service_name: Optional[str]
    filter_rules: dict
    retry_policy: dict
    active_flag: bool
    last_heartbeat: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventDeliveryResponse(BaseModel):
    delivery_id: UUID
    event_id: UUID
    subscription_id: UUID
    status: str
    delivery_attempts: int
    last_attempt_at: Optional[datetime]
    delivered_at: Optional[datetime]
    error_message: Optional[str]
    response_data: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventSearchQuery(BaseModel):
    event_type: Optional[str] = None
    status: Optional[EventStatus] = None
    correlation_id: Optional[str] = None
    aggregate_id: Optional[UUID] = None
    source_system: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class EventSearchResponse(BaseModel):
    events: List[EventResponse]
    total_count: int
    has_more: bool


class EventProcessResult(BaseModel):
    event_id: UUID
    status: EventStatus
    delivered_count: int
    failed_count: int
    error_message: Optional[str] = None
