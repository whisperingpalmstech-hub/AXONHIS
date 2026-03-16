"""Events module – system-wide event model and emission service.

Every clinical and operational action emits an Event, which:
- Populates the patient timeline
- Feeds the AI summarisation engine
- Drives notifications and audit analytics
"""
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventType(StrEnum):
    # Patient lifecycle
    PATIENT_REGISTERED = "PATIENT_REGISTERED"
    PATIENT_UPDATED = "PATIENT_UPDATED"

    # Encounter
    ENCOUNTER_OPENED = "ENCOUNTER_OPENED"
    ENCOUNTER_CLOSED = "ENCOUNTER_CLOSED"

    # Orders
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_APPROVED = "ORDER_APPROVED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    ORDER_COMPLETED = "ORDER_COMPLETED"

    # Tasks
    TASK_CREATED = "TASK_CREATED"
    TASK_COMPLETED = "TASK_COMPLETED"

    # Clinical
    VITALS_RECORDED = "VITALS_RECORDED"
    LAB_RESULT_AVAILABLE = "LAB_RESULT_AVAILABLE"
    MEDICATION_DISPENSED = "MEDICATION_DISPENSED"
    MEDICATION_ADMINISTERED = "MEDICATION_ADMINISTERED"
    IMAGING_RESULT_AVAILABLE = "IMAGING_RESULT_AVAILABLE"

    # Billing
    BILLING_ENTRY_CREATED = "BILLING_ENTRY_CREATED"
    BILLING_ENTRY_REVERSED = "BILLING_ENTRY_REVERSED"
    INVOICE_GENERATED = "INVOICE_GENERATED"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"

    # AI
    AI_SUMMARY_GENERATED = "AI_SUMMARY_GENERATED"
    VOICE_ORDER_SUGGESTED = "VOICE_ORDER_SUGGESTED"

    # User lifecycle
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"

    # Files
    FILE_UPLOADED = "FILE_UPLOADED"

    # Notifications
    NOTIFICATION_SENT = "NOTIFICATION_SENT"

    # Configuration
    CONFIG_CHANGED = "CONFIG_CHANGED"

    # Other
    DISCHARGE_PREPARED = "DISCHARGE_PREPARED"
    ALERT_RAISED = "ALERT_RAISED"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True
    )
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<Event type={self.event_type} patient={self.patient_id} at={self.occurred_at}>"
