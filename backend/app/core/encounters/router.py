"""Encounters router."""
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.encounters.schemas import EncounterCreate, EncounterDischarge, EncounterOut
from app.core.encounters.services import EncounterService
from app.core.events.models import EventType
from app.core.events.services import EventService
from app.core.events.models import Event
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/encounters", tags=["encounters"])


@router.post("", response_model=EncounterOut, status_code=status.HTTP_201_CREATED)
async def create_encounter(data: EncounterCreate, db: DBSession, user: CurrentUser) -> EncounterOut:
    encounter = await EncounterService(db).create(data, doctor_id=user.id)
    await EventService(db).emit(
        EventType.ENCOUNTER_OPENED,
        summary=f"{data.encounter_type} encounter opened",
        patient_id=data.patient_id,
        encounter_id=encounter.id,
        actor_id=user.id,
    )
    return EncounterOut.model_validate(encounter)


@router.get("/{encounter_id}", response_model=EncounterOut)
async def get_encounter(encounter_id: uuid.UUID, db: DBSession, _: CurrentUser) -> EncounterOut:
    encounter = await EncounterService(db).get_by_id(encounter_id)
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return EncounterOut.model_validate(encounter)


@router.get("/{encounter_id}/timeline")
async def get_timeline(encounter_id: uuid.UUID, db: DBSession, _: CurrentUser) -> list[dict]:
    """Return all events for this encounter ordered chronologically."""
    result = await db.execute(
        select(Event)
        .where(Event.encounter_id == encounter_id)
        .order_by(Event.occurred_at.asc())
    )
    events = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "type": e.event_type,
            "summary": e.summary,
            "occurred_at": e.occurred_at.isoformat(),
            "payload": e.payload,
        }
        for e in events
    ]


@router.post("/{encounter_id}/discharge", response_model=EncounterOut)
async def discharge_encounter(
    encounter_id: uuid.UUID, data: EncounterDischarge, db: DBSession, user: CurrentUser
) -> EncounterOut:
    service = EncounterService(db)
    encounter = await service.get_by_id(encounter_id)
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    encounter = await service.discharge(encounter, data.notes)
    await EventService(db).emit(
        EventType.ENCOUNTER_CLOSED,
        summary="Patient discharged",
        patient_id=encounter.patient_id,
        encounter_id=encounter.id,
        actor_id=user.id,
    )
    return EncounterOut.model_validate(encounter)
