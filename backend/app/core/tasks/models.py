"""Tasks module – Phase 5: Task & Care Execution Platform.

Models for:
- Task (enhanced with encounter_id, patient_id, scheduling)
- TaskStatusHistory (audit trail)
- TaskAssignment (staff assignments)
- TaskExecutionLog (completion records)
- TaskTemplate (reusable task definitions)
"""
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
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
    PATIENT_TRANSPORT = "PATIENT_TRANSPORT"
    VITAL_MONITORING = "VITAL_MONITORING"
    GENERIC = "GENERIC"


class TaskPriority(StrEnum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    STAT = "STAT"


# ─── TASK ────────────────────────────────────────────────────────────────
class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_uuid: Mapped[str] = mapped_column(String(50), unique=True, nullable=False,
                                            default=lambda: f"TSK-{uuid.uuid4().hex[:8].upper()}")
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default=TaskPriority.ROUTINE)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=TaskStatus.PENDING, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_to_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assigned_to_user: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    schedule_interval: Mapped[int | None] = mapped_column(Integer, nullable=True)  # minutes
    next_execution_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    assignments: Mapped[list["TaskAssignment"]] = relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    status_history: Mapped[list["TaskStatusHistory"]] = relationship("TaskStatusHistory", back_populates="task", cascade="all, delete-orphan")
    execution_logs: Mapped[list["TaskExecutionLog"]] = relationship("TaskExecutionLog", back_populates="task", cascade="all, delete-orphan")


# ─── TASK STATUS HISTORY ─────────────────────────────────────────────────
class TaskStatusHistory(Base):
    __tablename__ = "task_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    task: Mapped["Task"] = relationship("Task", back_populates="status_history")


# ─── TASK ASSIGNMENT ─────────────────────────────────────────────────────
class TaskAssignment(Base):
    __tablename__ = "task_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_to_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    task: Mapped["Task"] = relationship("Task", back_populates="assignments")


# ─── TASK EXECUTION LOG ─────────────────────────────────────────────────
class TaskExecutionLog(Base):
    __tablename__ = "task_execution_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    executed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    execution_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "medication_administered"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata_json", JSONB, nullable=False, default=dict)
    task: Mapped["Task"] = relationship("Task", back_populates="execution_logs")


# ─── TASK TEMPLATE ───────────────────────────────────────────────────────
class TaskTemplate(Base):
    __tablename__ = "task_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    default_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_priority: Mapped[str] = mapped_column(String(10), default=TaskPriority.ROUTINE)
    schedule_interval: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
