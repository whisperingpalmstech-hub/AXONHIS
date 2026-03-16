import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.encounters.timeline.models import EncounterTimeline
from app.core.encounters.timeline.schemas import EncounterTimelineCreate

class TimelineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_event(self, encounter_id: uuid.UUID, actor_id: uuid.UUID, data: EncounterTimelineCreate) -> EncounterTimeline:
        event = EncounterTimeline(
            encounter_id=encounter_id,
            actor_id=actor_id,
            event_type=data.event_type,
            description=data.description,
            metadata_json=data.metadata_json
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_timeline(self, encounter_id: uuid.UUID) -> Sequence[EncounterTimeline]:
        stmt = select(EncounterTimeline).where(EncounterTimeline.encounter_id == encounter_id).order_by(EncounterTimeline.event_time.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()
