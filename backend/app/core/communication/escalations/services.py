import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import TaskEscalation
from .schemas import TaskEscalationCreate
from app.core.communication.notifications.services import NotificationService
from app.core.communication.notifications.schemas import NotificationCreate


class EscalationService:
    @staticmethod
    async def create_escalation(db: AsyncSession, data: TaskEscalationCreate, escalated_by: uuid.UUID) -> TaskEscalation:
        escalation = TaskEscalation(
            task_id=data.task_id,
            escalated_by=escalated_by,
            escalated_to=data.escalated_to,
            reason=data.reason
        )
        db.add(escalation)
        await db.commit()
        await db.refresh(escalation)

        # Notify the person it was escalated to
        await NotificationService.create_notification(db, NotificationCreate(
            user_id=data.escalated_to,
            notification_type="task_escalation",
            reference_id=data.task_id,
            message=f"Task escalated by user {escalated_by}: {data.reason}"
        ))

        return escalation

    @staticmethod
    async def get_escalations(db: AsyncSession) -> list[TaskEscalation]:
        stmt = select(TaskEscalation).order_by(TaskEscalation.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())
