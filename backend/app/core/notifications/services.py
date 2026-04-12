"""Notification service – send, query, and manage notifications."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.notifications.models import Notification, NotificationChannel, NotificationStatus


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def send(
        self,
        user_id: uuid.UUID,
        title: str,
        message: str,
        notification_type: str = "INFO",
        channel: str = NotificationChannel.IN_APP,
        link: str | None = None,
    ) -> Notification:
        """Create and send a notification."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            channel=channel,
            link=link,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def send_to_many(
        self, user_ids: list[uuid.UUID], title: str, message: str,
        notification_type: str = "INFO", link: str | None = None,
    ) -> list[Notification]:
        """Send the same notification to multiple users."""
        notifications = []
        for uid in user_ids:
            n = Notification(
                user_id=uid, title=title, message=message,
                notification_type=notification_type, link=link,
            )
            self.db.add(n)
            notifications.append(n)
        await self.db.flush()
        return notifications

    async def get_for_user(
        self, user_id: uuid.UUID, status: str | None = None,
        skip: int = 0, limit: int = 20,
    ) -> tuple[list[Notification], int]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if status:
            stmt = stmt.where(Notification.status == status)

        count = (await self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        )).scalar_one()

        result = await self.db.execute(
            stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), count

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.status == NotificationStatus.UNREAD,
            )
        )
        return result.scalar_one()

    async def mark_read(self, notification_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        n = result.scalar_one_or_none()
        if n:
            n.status = NotificationStatus.READ
            n.read_at = datetime.now(timezone.utc)
            await self.db.flush()
            return True
        return False

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.status == NotificationStatus.UNREAD,
            )
        )
        notifications = list(result.scalars().all())
        now = datetime.now(timezone.utc)
        for n in notifications:
            n.status = NotificationStatus.READ
            n.read_at = now
        await self.db.flush()
        return len(notifications)
