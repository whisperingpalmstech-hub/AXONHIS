"""Tasks module – Task model for order-driven work assignment."""
import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskType(StrEnum):
    COLLECT_SPECIMEN = "COLLECT_SPECIMEN"
    PROCESS_LAB_TEST = "PROCESS_LAB_TEST"
    DISPENSE_MEDICATION = "DISPENSE_MEDICATION"
    ADMINISTER_MEDICATION = "ADMINISTER_MEDICATION"
    PERFORM_PROCEDURE = "PERFORM_PROCEDURE"
    PERFORM_IMAGING = "PERFORM_IMAGING"
    RECORD_VITALS = "RECORD_VITALS"
    PREPARE_DISCHARGE = "PREPARE_DISCHARGE"
    NURSING_ASSESSMENT = "NURSING_ASSESSMENT"
    GENERIC = "GENERIC"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=TaskStatus.PENDING)
    assigned_to_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assigned_to_user: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
