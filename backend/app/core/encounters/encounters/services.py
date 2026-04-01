import uuid
from typing import Sequence
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encounters.encounters.models import Encounter
from app.core.encounters.encounters.schemas import EncounterCreate, EncounterUpdate
from app.core.encounters.timeline.services import TimelineService
from app.core.encounters.timeline.schemas import EncounterTimelineCreate

from app.core.auth.models import User
from app.core.patients.patients.models import Patient

class EncounterService:
    def __init__(self, db: AsyncSession, user: User = None):
        self.db = db
        self.user = user

    def _apply_tenant_filter(self, stmt):
        if self.user and getattr(self.user, 'org_id', None):
            return stmt.join(Patient, Encounter.patient_id == Patient.id).where(Patient.org_id == self.user.org_id)
        return stmt

    async def create_encounter(self, data: EncounterCreate, author_id: uuid.UUID) -> Encounter:
        encounter_uuid = f"ENC-{uuid.uuid4().hex[:8].upper()}"
        
        start_time = None
        if data.status == "in_progress":
            start_time = datetime.utcnow()
            
        encounter = Encounter(
            encounter_uuid=encounter_uuid,
            patient_id=data.patient_id,
            encounter_type=data.encounter_type,
            doctor_id=data.doctor_id or author_id,
            department=data.department,
            status=data.status,
            start_time=start_time
        )
        self.db.add(encounter)
        await self.db.flush()

        # Generate automated timeline event
        ts = TimelineService(self.db)
        await ts.add_event(encounter.id, author_id, EncounterTimelineCreate(
            event_type="encounter_created",
            description=f"Encounter {encounter_uuid} created dynamically."
        ))

        return await self.get_encounter_by_id(encounter.id)

    async def get_encounter_by_id(self, encounter_id: uuid.UUID) -> Encounter | None:
        stmt = (
            select(Encounter)
            .options(
                selectinload(Encounter.diagnoses),
                selectinload(Encounter.notes),
                selectinload(Encounter.timeline_events)
            )
            .where(Encounter.id == encounter_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_encounter(self, encounter: Encounter, data: EncounterUpdate, author_id: uuid.UUID) -> Encounter:
        # Detect state changes securely
        old_status = encounter.status
        new_status = data.status or old_status

        if data.status:
            encounter.status = data.status
            if data.status == "in_progress" and not encounter.start_time:
                encounter.start_time = datetime.utcnow()
            elif data.status == "completed" and not encounter.end_time:
                encounter.end_time = datetime.utcnow()
                
        if data.department:
            encounter.department = data.department

        await self.db.flush()
        
        # Log timeline if state changes
        if old_status != new_status:
            ts = TimelineService(self.db)
            await ts.add_event(encounter.id, author_id, EncounterTimelineCreate(
                event_type=f"consultation_{new_status}",
                description=f"Encounter status moved to {new_status}."
            ))

        return await self.get_encounter_by_id(encounter.id)

    async def list_encounters(self, skip: int = 0, limit: int = 20) -> Sequence[Encounter]:
        stmt = (
            select(Encounter)
            .options(
                selectinload(Encounter.diagnoses),
                selectinload(Encounter.notes),
                selectinload(Encounter.timeline_events)
            )
            .order_by(Encounter.created_at.desc())
        )
        stmt = self._apply_tenant_filter(stmt)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().unique().all()
