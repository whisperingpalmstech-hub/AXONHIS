"""Task services – auto-generates tasks from approved orders."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.orders.models import Order, OrderType
from app.core.tasks.models import Task, TaskStatus, TaskType


# Map order types to the tasks they produce
ORDER_TASK_MAP: dict[str, list[dict]] = {
    OrderType.LAB_ORDER: [
        {"task_type": TaskType.COLLECT_SPECIMEN, "role": "NURSE", "desc": "Collect specimen for lab test"},
        {"task_type": TaskType.PROCESS_LAB_TEST, "role": "LAB_TECH", "desc": "Process lab test and enter results"},
    ],
    OrderType.MEDICATION_ORDER: [
        {"task_type": TaskType.DISPENSE_MEDICATION, "role": "PHARMACIST", "desc": "Dispense medication"},
        {"task_type": TaskType.ADMINISTER_MEDICATION, "role": "NURSE", "desc": "Administer medication to patient"},
    ],
    OrderType.RADIOLOGY_ORDER: [
        {"task_type": TaskType.PERFORM_IMAGING, "role": "LAB_TECH", "desc": "Perform imaging study"},
    ],
    OrderType.PROCEDURE_ORDER: [
        {"task_type": TaskType.PERFORM_PROCEDURE, "role": "DOCTOR", "desc": "Perform clinical procedure"},
    ],
    OrderType.NURSING_TASK: [
        {"task_type": TaskType.NURSING_ASSESSMENT, "role": "NURSE", "desc": "Complete nursing assessment"},
    ],
    OrderType.DISCHARGE_ORDER: [
        {"task_type": TaskType.PREPARE_DISCHARGE, "role": "NURSE", "desc": "Prepare patient for discharge"},
    ],
}


class TaskService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def generate_tasks(self, order: Order) -> list[Task]:
        """Auto-generate tasks from an approved order based on order type → task mapping."""
        task_defs = ORDER_TASK_MAP.get(order.order_type, [
            {"task_type": TaskType.GENERIC, "role": None, "desc": f"Execute {order.order_type}"}
        ])
        tasks = []
        for td in task_defs:
            task = Task(
                order_id=order.id,
                task_type=td["task_type"],
                description=td["desc"],
                assigned_to_role=td["role"],
            )
            self.db.add(task)
            tasks.append(task)
        await self.db.flush()
        return tasks

    async def get_by_id(self, task_id: uuid.UUID) -> Task | None:
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def get_by_order(self, order_id: uuid.UUID) -> list[Task]:
        result = await self.db.execute(
            select(Task).where(Task.order_id == order_id).order_by(Task.created_at)
        )
        return list(result.scalars().all())

    async def complete_task(self, task: Task, completed_by: uuid.UUID, notes: str | None = None) -> Task:
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        task.completed_by = completed_by
        if notes:
            task.notes = notes
        await self.db.flush()
        return task
