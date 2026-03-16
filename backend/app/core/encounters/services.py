"""Encounter services."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encounters.models import Encounter, EncounterStatus
from app.core.encounters.schemas import EncounterCreate


class EncounterService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: EncounterCreate, doctor_id: uuid.UUID) -> Encounter:
        encounter = Encounter(**data.model_dump(), doctor_id=doctor_id)
        self.db.add(encounter)
        await self.db.flush()
        return encounter

    async def get_by_id(self, encounter_id: uuid.UUID) -> Encounter | None:
        result = await self.db.execute(select(Encounter).where(Encounter.id == encounter_id))
        return result.scalar_one_or_none()

    async def get_by_patient(self, patient_id: uuid.UUID) -> list[Encounter]:
        result = await self.db.execute(
            select(Encounter)
            .where(Encounter.patient_id == patient_id)
            .order_by(Encounter.admitted_at.desc())
        )
        return list(result.scalars().all())

    async def discharge(self, encounter: Encounter, notes: str | None = None) -> Encounter:
        encounter.status = EncounterStatus.DISCHARGED
        encounter.discharged_at = datetime.now(timezone.utc)
        if notes:
            encounter.notes = notes
        await self.db.flush()
        return encounter
