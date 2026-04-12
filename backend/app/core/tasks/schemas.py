"""Tasks schemas."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.tasks.models import TaskPriority, TaskStatus, TaskType


# ─── TASK EXECUTION LOG ──────────────────────────────────────────────────
class TaskExecutionLogOut(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    executed_by: uuid.UUID
    execution_time: datetime
    action: str
    notes: str | None = None
    metadata_json: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class TaskExecutionLogCreate(BaseModel):
    action: str
    notes: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


# ─── TASK ASSIGNMENT ─────────────────────────────────────────────────────
class TaskAssignmentOut(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    assigned_to_user_id: uuid.UUID
    assigned_by: uuid.UUID | None = None
    assigned_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TaskAssignmentCreate(BaseModel):
    assigned_to_user_id: uuid.UUID


# ─── TASK STATUS HISTORY ─────────────────────────────────────────────────
class TaskStatusHistoryOut(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    status: str
    changed_by: uuid.UUID | None = None
    notes: str | None = None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── TASK ────────────────────────────────────────────────────────────────
class TaskBase(BaseModel):
    task_type: TaskType
    priority: TaskPriority = TaskPriority.ROUTINE
    description: str
    instructions: str | None = None
    assigned_to_role: str | None = None
    assigned_to_user: uuid.UUID | None = None
    due_at: datetime | None = None
    schedule_interval: int | None = Field(None, description="Interval in minutes for recurring tasks")


class TaskCreate(TaskBase):
    order_id: uuid.UUID
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")

    model_config = ConfigDict(populate_by_name=True)


class TaskUpdate(BaseModel):
    priority: TaskPriority | None = None
    instructions: str | None = None
    assigned_to_role: str | None = None
    assigned_to_user: uuid.UUID | None = None
    due_at: datetime | None = None


class TaskCompleteReq(BaseModel):
    notes: str | None = None
    action: str = "completed"
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class TaskOut(TaskBase):
    id: uuid.UUID
    task_uuid: str
    order_id: uuid.UUID
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
    status: TaskStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    completed_by: uuid.UUID | None = None
    notes: str | None = None
    next_execution_time: datetime | None = None
    metadata_: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_")
    created_at: datetime
    updated_at: datetime

    assignments: list[TaskAssignmentOut] = []
    status_history: list[TaskStatusHistoryOut] = []
    execution_logs: list[TaskExecutionLogOut] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ─── TASK TEMPLATE ───────────────────────────────────────────────────────
class TaskTemplateBase(BaseModel):
    template_name: str
    description: str | None = None
    task_type: TaskType
    default_instructions: str | None = None
    default_priority: TaskPriority = TaskPriority.ROUTINE
    schedule_interval: int | None = None


class TaskTemplateCreate(TaskTemplateBase):
    pass


class TaskTemplateUpdate(BaseModel):
    template_name: str | None = None
    description: str | None = None
    task_type: TaskType | None = None
    default_instructions: str | None = None
    default_priority: TaskPriority | None = None
    schedule_interval: int | None = None
    is_active: bool | None = None


class TaskTemplateOut(TaskTemplateBase):
    id: uuid.UUID
    created_by: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
