from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Numeric, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class EventStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class EventType(str, enum.Enum):
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


class MdEvent(Base):
    """
    Event Bus model for operational events.
    Supports event-driven architecture for automation and integration.
    """
    __tablename__ = "md_event"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    event_name = Column(String(255), nullable=False)
    event_version = Column(String(20), default="1.0", nullable=False)
    correlation_id = Column(String(100), nullable=True, index=True)  # Links related events
    causation_id = Column(String(100), nullable=True)  # Event that caused this event
    source_system = Column(String(50), nullable=False)  # System that generated the event
    source_type = Column(String(50), nullable=False)  # API, service, external system
    aggregate_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # ID of the entity
    aggregate_type = Column(String(50), nullable=True, index=True)  # Type of entity
    payload = Column(JSONB, nullable=False, default={})
    meta_data = Column(JSONB, nullable=False, default={})
    status = Column(SQLEnum(EventStatus), default=EventStatus.PENDING, nullable=False, index=True)
    retry_count = Column(Numeric(3,0), default=0, nullable=False)
    max_retries = Column(Numeric(3,0), default=3, nullable=False)
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index('idx_event_status_created', 'status', 'created_at'),
        Index('idx_event_type_status', 'event_type', 'status'),
        Index('idx_event_correlation', 'correlation_id', 'created_at'),
    )


class MdEventSubscription(Base):
    """
    Event subscription model for event consumers.
    Defines which events a consumer is subscribed to and how to handle them.
    """
    __tablename__ = "md_event_subscription"

    subscription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscriber_name = Column(String(255), nullable=False, unique=True)
    subscriber_type = Column(String(50), nullable=False)  # webhook, service, queue
    event_types = Column(JSONB, nullable=False, default=[])  # List of event types to subscribe to
    endpoint_url = Column(String(500), nullable=True)  # For webhooks
    queue_name = Column(String(255), nullable=True)  # For message queues
    service_name = Column(String(255), nullable=True)  # For internal services
    filter_rules = Column(JSONB, nullable=False, default={})  # Filtering rules for events
    retry_policy = Column(JSONB, nullable=False, default={})  # Retry configuration
    active_flag = Column(Boolean, default=True, nullable=False)
    last_heartbeat = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class MdEventDelivery(Base):
    """
    Event delivery tracking model.
    Tracks delivery of events to subscribers.
    """
    __tablename__ = "md_event_delivery"

    delivery_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("md_event.event_id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("md_event_subscription.subscription_id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), default="PENDING", nullable=False, index=True)  # PENDING, DELIVERED, FAILED
    delivery_attempts = Column(Numeric(3,0), default=0, nullable=False)
    last_attempt_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    response_data = Column(JSONB, nullable=False, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    event = relationship("MdEvent", backref="deliveries")
    subscription = relationship("MdEventSubscription", backref="deliveries")

    __table_args__ = (
        Index('idx_delivery_event_subscription', 'event_id', 'subscription_id'),
        Index('idx_delivery_status', 'status', 'created_at'),
    )


class MdEventDeadLetter(Base):
    """
    Dead letter queue for failed events.
    Stores events that failed after max retries for manual inspection.
    """
    __tablename__ = "md_event_dead_letter"

    dead_letter_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_event_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String(50), nullable=False)
    event_payload = Column(JSONB, nullable=False, default={})
    failure_reason = Column(Text, nullable=False)
    failure_count = Column(Numeric(3,0), nullable=False)
    original_created_at = Column(DateTime, nullable=False)
    archived_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)

    __table_args__ = (
        Index('idx_dead_letter_resolved', 'resolved', 'archived_at'),
        Index('idx_dead_letter_type', 'event_type'),
    )
