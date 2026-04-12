import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Channel, ChannelMember, ChannelMessage
from .schemas import ChannelCreate, ChannelMessageCreate


class ChannelService:
    @staticmethod
    async def create_channel(db: AsyncSession, data: ChannelCreate, created_by: uuid.UUID) -> Channel:
        channel = Channel(
            channel_name=data.channel_name,
            department=data.department,
            created_by=created_by
        )
        db.add(channel)
        await db.commit()
        await db.refresh(channel)

        # Add creator as a member
        await ChannelService.add_member(db, channel.id, created_by)

        return channel

    @staticmethod
    async def get_channel(db: AsyncSession, channel_id: uuid.UUID) -> Channel | None:
        return await db.get(Channel, channel_id)

    @staticmethod
    async def get_channels(db: AsyncSession) -> list[Channel]:
        result = await db.execute(select(Channel))
        return list(result.scalars().all())

    @staticmethod
    async def add_member(db: AsyncSession, channel_id: uuid.UUID, user_id: uuid.UUID) -> ChannelMember:
        member = ChannelMember(channel_id=channel_id, user_id=user_id)
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def send_message(db: AsyncSession, data: ChannelMessageCreate, sender_id: uuid.UUID) -> ChannelMessage:
        message = ChannelMessage(
            channel_id=data.channel_id,
            sender_id=sender_id,
            message_content=data.message_content
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def get_messages(db: AsyncSession, channel_id: uuid.UUID) -> list[ChannelMessage]:
        stmt = select(ChannelMessage).where(ChannelMessage.channel_id == channel_id).order_by(ChannelMessage.created_at)
        result = await db.execute(stmt)
        return list(result.scalars().all())
