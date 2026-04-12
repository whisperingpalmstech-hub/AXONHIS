from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Boolean, Integer, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class WebhookStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class WebhookEventType(str, enum.Enum):
    ENCOUNTER_CREATED = "ENCOUNTER_CREATED"
    ENCOUNTER_UPDATED = "ENCOUNTER_UPDATED"
    PATIENT_CREATED = "PATIENT_CREATED"
    PATIENT_UPDATED = "PATIENT_UPDATED"
    DIAGNOSIS_ADDED = "DIAGNOSIS_ADDED"
    MEDICATION_ORDERED = "MEDICATION_ORDERED"
    LAB_RESULT_READY = "LAB_RESULT_READY"
    DOCUMENT_GENERATED = "DOCUMENT_GENERATED"
    CUSTOM = "CUSTOM"


class MdWebhookSubscription(Base):
    """
    Webhook subscription model for external integrations.
    Allows external systems to subscribe to events via webhooks.
    """
    __tablename__ = "md_webhook_subscription"

    subscription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_name = Column(String(255), nullable=False, unique=True)
    subscriber_name = Column(String(255), nullable=False)
    webhook_url = Column(String(500), nullable=False)
    secret_key = Column(String(255), nullable=True)  # For HMAC signature verification
    event_types = Column(JSONB, nullable=False, default=[])  # List of event types to subscribe to
    headers = Column(JSONB, nullable=False, default={})  # Custom headers to include
    status = Column(String(30), default=WebhookStatus.ACTIVE, nullable=False, index=True)
    retry_policy = Column(JSONB, nullable=False, default={})  # Retry configuration
    timeout_seconds = Column(Integer, default=30, nullable=False)
    verify_ssl = Column(Boolean, default=True, nullable=False)
    filter_rules = Column(JSONB, nullable=False, default={})  # Event filtering rules
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_triggered_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_webhook_status', 'status'),
        Index('idx_webhook_event_types', 'event_types'),
    )


class MdWebhookDelivery(Base):
    """
    Webhook delivery tracking model.
    Tracks delivery attempts and results for webhook events.
    """
    __tablename__ = "md_webhook_delivery"

    delivery_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("md_webhook_subscription.subscription_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    event_id = Column(UUID(as_uuid=True), nullable=True)  # ID of the source event
    payload = Column(JSONB, nullable=False, default={})
    status = Column(String(30), default="PENDING", nullable=False, index=True)  # PENDING, SUCCESS, FAILED, RETRYING
    http_status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempt_count = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    subscription = relationship("MdWebhookSubscription", backref="deliveries")

    __table_args__ = (
        Index('idx_webhook_delivery_subscription', 'subscription_id', 'created_at'),
        Index('idx_webhook_delivery_status', 'status', 'created_at'),
    )


class MdWebhookLog(Base):
    """
    Webhook activity log model.
    Logs all webhook activity for auditing and debugging.
    """
    __tablename__ = "md_webhook_log"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("md_webhook_subscription.subscription_id", ondelete="CASCADE"), nullable=True, index=True)
    delivery_id = Column(UUID(as_uuid=True), ForeignKey("md_webhook_delivery.delivery_id", ondelete="CASCADE"), nullable=True, index=True)
    log_level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    details = Column(JSONB, nullable=False, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    subscription = relationship("MdWebhookSubscription", backref="logs")
    delivery = relationship("MdWebhookDelivery", backref="logs")

    __table_args__ = (
        Index('idx_webhook_log_subscription_time', 'subscription_id', 'created_at'),
    )
