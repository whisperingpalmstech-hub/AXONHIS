import uuid
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Message, MessageStatus
from .schemas import MessageCreate
from app.core.communication.notifications.services import NotificationService as CommNotificationService
from app.core.communication.notifications.schemas import NotificationCreate as CommNotificationCreate
from app.core.notifications.services import NotificationService as GlobalNotificationService


class MessageService:
    @staticmethod
    async def send_message(db: AsyncSession, data: MessageCreate, sender_id: uuid.UUID) -> Message:
        message = Message(
            sender_id=sender_id,
            receiver_id=data.receiver_id,
            message_content=data.message_content,
            message_type=data.message_type.value,
            status=MessageStatus.SENT.value
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)

        # 1. Trigger internal Communication Notification for Receiver
        await CommNotificationService.create_notification(db, CommNotificationCreate(
            user_id=data.receiver_id,
            notification_type="new_message",
            reference_id=message.id,
            message=f"New message received"
        ))

        # 1.5. Trigger internal Communication Notification for Sender (Testing Visibility)
        await CommNotificationService.create_notification(db, CommNotificationCreate(
            user_id=sender_id,
            notification_type="sent_confirmation",
            reference_id=message.id,
            message=f"Message sent successfully to recipient."
        ))

        # 2. Trigger Global System Notification (Core Module - for Sidebar/Badge)
        global_service = GlobalNotificationService(db)
        await global_service.send(
            user_id=data.receiver_id,
            title="Communication Hub",
            message=f"You have a new message: {data.message_content[:30]}...",
            notification_type="INFO",
            link="/communication"
        )
        await db.commit()

        return message

    @staticmethod
    async def get_messages(db: AsyncSession, user1_id: uuid.UUID, user2_id: uuid.UUID) -> list[Message]:
        stmt = select(Message).where(
            or_(
                and_(Message.sender_id == user1_id, Message.receiver_id == user2_id),
                and_(Message.sender_id == user2_id, Message.receiver_id == user1_id)
            )
        ).order_by(Message.created_at)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def mark_read(db: AsyncSession, message_id: uuid.UUID) -> Message | None:
        message = await db.get(Message, message_id)
        if message and message.status != MessageStatus.READ.value:
            message.status = MessageStatus.READ.value
            await db.commit()
            await db.refresh(message)
        return message
