"""Tasks router – list, complete, and manage tasks."""
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.events.models import EventType
from app.core.events.services import EventService
from app.core.tasks.models import Task, TaskStatus
from app.core.tasks.services import TaskService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    task_type: str
    description: str
    status: str
    assigned_to_role: str | None
    assigned_to_user: uuid.UUID | None
    notes: str | None
    created_at: str

    model_config = {"from_attributes": True}


class TaskComplete(BaseModel):
    notes: str | None = None


@router.get("/order/{order_id}", response_model=list[TaskOut])
async def list_tasks_for_order(order_id: uuid.UUID, db: DBSession, _: CurrentUser) -> list[TaskOut]:
    tasks = await TaskService(db).get_by_order(order_id)
    return [TaskOut.model_validate(t) for t in tasks]


@router.post("/{task_id}/complete", response_model=TaskOut)
async def complete_task(
    task_id: uuid.UUID, data: TaskComplete, db: DBSession, user: CurrentUser
) -> TaskOut:
    service = TaskService(db)
    task = await service.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Task already completed")

    task = await service.complete_task(task, completed_by=user.id, notes=data.notes)
    await EventService(db).emit(
        EventType.TASK_COMPLETED,
        summary=f"Task '{task.task_type}' completed",
        actor_id=user.id,
        payload={"task_id": str(task.id), "order_id": str(task.order_id)},
    )
    return TaskOut.model_validate(task)
