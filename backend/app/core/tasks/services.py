"""Task services – Phase 5: Task lifecycle, assignment, and execution."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.orders.models import Order, OrderType
from app.core.tasks.models import (
    Task,
    TaskAssignment,
    TaskExecutionLog,
    TaskPriority,
    TaskStatus,
    TaskStatusHistory,
    TaskType,
    TaskTemplate,
)


ORDER_TASK_MAP: dict[str, list[dict]] = {
    OrderType.LAB_ORDER: [
        {"task_type": TaskType.COLLECT_SPECIMEN, "role": "nurse", "desc": "Collect specimen for lab test", "priority": TaskPriority.ROUTINE},
        {"task_type": TaskType.PROCESS_LAB_TEST, "role": "lab_tech", "desc": "Process lab test", "priority": TaskPriority.ROUTINE},
    ],
    OrderType.MEDICATION_ORDER: [
        {"task_type": TaskType.DISPENSE_MEDICATION, "role": "pharmacist", "desc": "Dispense medication", "priority": TaskPriority.ROUTINE},
        {"task_type": TaskType.ADMINISTER_MEDICATION, "role": "nurse", "desc": "Administer medication", "priority": TaskPriority.ROUTINE},
    ],
    OrderType.RADIOLOGY_ORDER: [
        {"task_type": TaskType.PERFORM_IMAGING, "role": "radiology_tech", "desc": "Perform imaging study", "priority": TaskPriority.ROUTINE},
    ],
    OrderType.PROCEDURE_ORDER: [
        {"task_type": TaskType.PERFORM_PROCEDURE, "role": "doctor", "desc": "Perform clinical procedure", "priority": TaskPriority.ROUTINE},
    ],
    OrderType.NURSING_TASK: [
        {"task_type": TaskType.NURSING_ASSESSMENT, "role": "nurse", "desc": "Nursing assessment", "priority": TaskPriority.ROUTINE},
    ],
    OrderType.DISCHARGE_ORDER: [
        {"task_type": TaskType.PREPARE_DISCHARGE, "role": "nurse", "desc": "Prepare patient for discharge", "priority": TaskPriority.ROUTINE},
    ],
    OrderType.ADMISSION_ORDER: [
        {"task_type": TaskType.VITAL_MONITORING, "role": "nurse", "desc": "Initial admission vitals", "priority": TaskPriority.ROUTINE},
        {"task_type": TaskType.NURSING_ASSESSMENT, "role": "nurse", "desc": "Admission assessment", "priority": TaskPriority.ROUTINE},
    ]
}


from app.core.auth.models import User
from app.core.patients.patients.models import Patient

class TaskService:
    def __init__(self, db: AsyncSession, user: User = None) -> None:
        self.db = db
        self.user = user

    def _apply_tenant_filter(self, stmt):
        if self.user and getattr(self.user, 'org_id', None):
            return stmt.join(Patient, Task.patient_id == Patient.id).where(Patient.org_id == self.user.org_id)
        return stmt

    async def _log_status_change(self, task_id: uuid.UUID, status: str, user_id: uuid.UUID | None, notes: str | None = None) -> None:
        history = TaskStatusHistory(task_id=task_id, status=status, changed_by=user_id, notes=notes)
        self.db.add(history)

    async def generate_tasks_for_order(self, order: Order, user_id: uuid.UUID | None = None) -> list[Task]:
        """Auto-generate tasks from an approved order based on mapping."""
        # Use order priority if mapped tasks don't specify, or default logic
        order_prio = getattr(order, "priority", TaskPriority.ROUTINE)

        task_defs = ORDER_TASK_MAP.get(order.order_type, [
            {"task_type": TaskType.GENERIC, "role": None, "desc": f"Execute {order.order_type}", "priority": order_prio}
        ])

        tasks = []
        for td in task_defs:
            task = Task(
                order_id=order.id,
                patient_id=order.patient_id,
                encounter_id=order.encounter_id,
                task_type=td["task_type"],
                description=f"{td['desc']} - {order.notes or 'No special notes'}",
                priority=order_prio if order_prio in [TaskPriority.STAT, TaskPriority.URGENT] else td.get("priority", TaskPriority.ROUTINE),
                assigned_to_role=td["role"],
                status=TaskStatus.PENDING,
            )
            self.db.add(task)
            await self.db.flush()  # To get task.id
            await self._log_status_change(task.id, TaskStatus.PENDING, user_id, "Auto-generated from order")
            tasks.append(task)
        
        await self.db.commit()
        return tasks

    async def get_by_id(self, task_id: uuid.UUID) -> Task | None:
        stmt = (
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.assignments),
                selectinload(Task.status_history),
                selectinload(Task.execution_logs),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_tasks(self, encounter_id: uuid.UUID | None = None, role: str | None = None, status: str | None = None) -> list[Task]:
        stmt = select(Task).options(
            selectinload(Task.assignments),
            selectinload(Task.status_history),
            selectinload(Task.execution_logs),
        )
        if encounter_id:
            stmt = stmt.where(Task.encounter_id == encounter_id)
        if role:
            stmt = stmt.where(Task.assigned_to_role == role)
        if status:
            stmt = stmt.where(Task.status == status)
        
        stmt = self._apply_tenant_filter(stmt)
        stmt = stmt.order_by(Task.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_my_tasks(self, user_id: uuid.UUID) -> list[Task]:
        """Get tasks directly assigned to a user."""
        stmt = (
            select(Task)
            .join(TaskAssignment, Task.id == TaskAssignment.task_id)
            .where(TaskAssignment.assigned_to_user_id == user_id, TaskAssignment.is_active == True)
            .where(Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]))
            .options(
                selectinload(Task.assignments),
                selectinload(Task.status_history),
                selectinload(Task.execution_logs),
            )
            .order_by(Task.due_at.asc().nulls_last())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def assign_task(self, task: Task, user_id: uuid.UUID, assigned_by: uuid.UUID | None = None) -> Task:
        # Invalidate old active assignments
        for a in task.assignments:
            if a.is_active:
                a.is_active = False

        assignment = TaskAssignment(
            task_id=task.id,
            assigned_to_user_id=user_id,
            assigned_by=assigned_by
        )
        self.db.add(assignment)
        
        task.status = TaskStatus.ASSIGNED
        task.assigned_to_user = user_id
        await self._log_status_change(task.id, TaskStatus.ASSIGNED, assigned_by, f"Assigned to user {user_id}")
        await self.db.flush()
        return task

    async def start_task(self, task: Task, user_id: uuid.UUID) -> Task:
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now(timezone.utc)
        await self._log_status_change(task.id, TaskStatus.IN_PROGRESS, user_id, "Task started")
        await self.db.flush()
        return task

    async def complete_task(self, task: Task, user_id: uuid.UUID, action: str, notes: str | None = None, metadata_json: dict | None = None) -> Task:
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        task.completed_by = user_id
        task.notes = notes

        # Add execution log
        log = TaskExecutionLog(
            task_id=task.id,
            executed_by=user_id,
            action=action,
            notes=notes,
            metadata_json=metadata_json or {}
        )
        self.db.add(log)
        
        await self._log_status_change(task.id, TaskStatus.COMPLETED, user_id, f"Completed: {action}")
        
        # Handle recurring tasks
        if task.schedule_interval:
            task.next_execution_time = datetime.now(timezone.utc) + timedelta(minutes=task.schedule_interval)
            # Revert status to assigned if there's an interval, so it pops up again. 
            # OR generate a new child task. In Phase 5, creating a new task is cleaner for history.
            next_task = Task(
                order_id=task.order_id,
                patient_id=task.patient_id,
                encounter_id=task.encounter_id,
                task_type=task.task_type,
                description=task.description,
                priority=task.priority,
                instructions=task.instructions,
                assigned_to_role=task.assigned_to_role,
                assigned_to_user=task.assigned_to_user,
                due_at=task.next_execution_time,
                schedule_interval=task.schedule_interval,
                status=TaskStatus.ASSIGNED if task.assigned_to_user else TaskStatus.PENDING,
            )
            self.db.add(next_task)
            await self.db.flush()
            await self._log_status_change(next_task.id, next_task.status, user_id, "Auto-generated recurring task")
            
            # Carry over active assignments to the new recurring task
            active_assigns = [a for a in task.assignments if a.is_active]
            for a in active_assigns:
                self.db.add(TaskAssignment(
                    task_id=next_task.id, assigned_to_user_id=a.assigned_to_user_id, assigned_by=a.assigned_by
                ))

        await self.db.commit()
        
        # Refresh task
        stmt = select(Task).where(Task.id == task.id).options(selectinload(Task.assignments), selectinload(Task.status_history), selectinload(Task.execution_logs))
        res = await self.db.execute(stmt)
        return res.scalar_one()

    async def cancel_task(self, task: Task, user_id: uuid.UUID, reason: str) -> Task:
        task.status = TaskStatus.CANCELLED
        task.notes = f"Cancelled: {reason}"
        await self._log_status_change(task.id, TaskStatus.CANCELLED, user_id, reason)
        await self.db.flush()
        return task


class TaskTemplateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        
    async def create(self, user_id: uuid.UUID, data: dict) -> TaskTemplate:
        template = TaskTemplate(**data, created_by=user_id)
        self.db.add(template)
        await self.db.flush()
        return template

    async def list_all(self, active_only: bool = True) -> list[TaskTemplate]:
        stmt = select(TaskTemplate)
        if active_only:
            stmt = stmt.where(TaskTemplate.is_active == True)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, template_id: uuid.UUID) -> TaskTemplate | None:
        result = await self.db.execute(select(TaskTemplate).where(TaskTemplate.id == template_id))
        return result.scalar_one_or_none()
