import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import CommunicationNotification, NotificationStatus
from .schemas import NotificationCreate


class NotificationService:
    @staticmethod
    async def create_notification(db: AsyncSession, data: NotificationCreate) -> CommunicationNotification:
        notification = CommunicationNotification(**data.model_dump())
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    @staticmethod
    async def get_user_notifications(db: AsyncSession, user_id: uuid.UUID) -> list[CommunicationNotification]:
        stmt = select(CommunicationNotification).where(CommunicationNotification.user_id == user_id).order_by(CommunicationNotification.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def mark_as_read(db: AsyncSession, notification_id: uuid.UUID) -> CommunicationNotification | None:
        notification = await db.get(CommunicationNotification, notification_id)
        if notification and notification.status != NotificationStatus.READ.value:
            notification.status = NotificationStatus.READ.value
            await db.commit()
            await db.refresh(notification)
        return notification
