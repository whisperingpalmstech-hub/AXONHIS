import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import PostoperativeEvent
from .schemas import PostoperativeEventCreate


class PostoperativeEventService:
    @staticmethod
    async def record_event(db: AsyncSession, event_in: PostoperativeEventCreate) -> PostoperativeEvent:
        event = PostoperativeEvent(**event_in.model_dump())
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    @staticmethod
    async def get_events_for_schedule(db: AsyncSession, schedule_id: uuid.UUID) -> list[PostoperativeEvent]:
        stmt = select(PostoperativeEvent).where(PostoperativeEvent.schedule_id == schedule_id).order_by(PostoperativeEvent.event_time)
        result = await db.execute(stmt)
        return list(result.scalars().all())
