"""EventService – shared service used by every module to emit events."""
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.models import Event, EventType


class EventService:
    """
    Emit structured events that build the patient timeline.

    Usage:
        await EventService(db).emit(
            event_type=EventType.ORDER_APPROVED,
            summary="Lab order for CBC approved by Dr. Smith",
            patient_id=patient.id,
            encounter_id=encounter.id,
            actor_id=current_user.id,
            payload={"order_id": str(order.id)},
        )
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def emit(
        self,
        event_type: EventType,
        summary: str,
        patient_id: uuid.UUID | None = None,
        encounter_id: uuid.UUID | None = None,
        actor_id: uuid.UUID | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Event:
        event = Event(
            event_type=event_type,
            summary=summary,
            patient_id=patient_id,
            encounter_id=encounter_id,
            actor_id=actor_id,
            payload=payload or {},
        )
        self.db.add(event)
        await self.db.flush()
        return event
