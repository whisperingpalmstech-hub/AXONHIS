"""Tasks router – Phase 5: Complete task lifecycle and assignments."""
import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.core.events.models import EventType
from app.core.events.services import EventService
from app.core.tasks.models import TaskPriority, TaskStatus
from app.core.tasks.schemas import (
    TaskAssignmentCreate,
    TaskCompleteReq,
    TaskCreate,
    TaskOut,
    TaskTemplateCreate,
    TaskTemplateOut,
    TaskTemplateUpdate,
    TaskUpdate,
)
from app.core.tasks.services import TaskService, TaskTemplateService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/tasks", tags=["tasks"])


# ─── TASK TEMPLATES ──────────────────────────────────────────────────────
@router.get("/templates", response_model=list[TaskTemplateOut])
async def list_task_templates(
    db: DBSession, _: CurrentUser, active_only: bool = Query(True)
):
    return await TaskTemplateService(db).list_all(active_only=active_only)


@router.post("/templates", response_model=TaskTemplateOut, status_code=status.HTTP_201_CREATED)
async def create_task_template(
    data: TaskTemplateCreate, db: DBSession, user: CurrentUser
):
    template = await TaskTemplateService(db).create(user.id, data.model_dump())
    return TaskTemplateOut.model_validate(template)


# ─── TASKS ───────────────────────────────────────────────────────────────
@router.get("", response_model=list[TaskOut])
async def list_tasks(
    db: DBSession,
    user: CurrentUser,
    encounter_id: uuid.UUID | None = None,
    role: str | None = None,
    status: str | None = None,
):
    tasks = await TaskService(db, user).list_tasks(encounter_id, role, status)
    return [TaskOut.model_validate(t) for t in tasks]


@router.get("/my-tasks", response_model=list[TaskOut])
async def list_my_tasks(db: DBSession, user: CurrentUser):
    tasks = await TaskService(db, user).get_my_tasks(user.id)
    return [TaskOut.model_validate(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: uuid.UUID, db: DBSession, _: CurrentUser):
    task = await TaskService(db).get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut.model_validate(task)


@router.post("/{task_id}/assign", response_model=TaskOut)
async def assign_task(
    task_id: uuid.UUID, data: TaskAssignmentCreate, db: DBSession, user: CurrentUser
):
    service = TaskService(db)
    task = await service.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Cannot assign a completed/cancelled task")
        
    task = await service.assign_task(task, data.assigned_to_user_id, assigned_by=user.id)
    return TaskOut.model_validate(task)


@router.post("/{task_id}/start", response_model=TaskOut)
async def start_task(task_id: uuid.UUID, db: DBSession, user: CurrentUser):
    service = TaskService(db)
    task = await service.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != TaskStatus.ASSIGNED:
        raise HTTPException(status_code=400, detail="Task must be ASSIGNED before it can be started")
        
    task = await service.start_task(task, user.id)
    return TaskOut.model_validate(task)


@router.post("/{task_id}/complete", response_model=TaskOut)
async def complete_task(
    task_id: uuid.UUID, data: TaskCompleteReq, db: DBSession, user: CurrentUser
):
    service = TaskService(db)
    task = await service.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Task already completed")

    task = await service.complete_task(
        task, user_id=user.id, action=data.action, notes=data.notes, metadata_json=data.metadata_json
    )
    
    # Emit event suitable for the timeline
    event_summary = f"Task completed: {task.description}"
    await EventService(db).emit(
        EventType.TASK_COMPLETED,
        summary=event_summary,
        actor_id=user.id,
        patient_id=task.patient_id,
        encounter_id=task.encounter_id,
        payload={"task_id": str(task.id), "order_id": str(task.order_id), "action": data.action},
    )
    return TaskOut.model_validate(task)
