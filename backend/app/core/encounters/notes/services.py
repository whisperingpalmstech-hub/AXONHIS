import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.encounters.notes.models import EncounterNote
from app.core.encounters.notes.schemas import EncounterNoteCreate

class NoteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_note(self, encounter_id: uuid.UUID, author_id: uuid.UUID, data: EncounterNoteCreate, org_id: uuid.UUID = None) -> EncounterNote:
        note = EncounterNote(
            encounter_id=encounter_id,
            note_type=data.note_type,
            content=data.content,
            created_by=author_id
        )
        self.db.add(note)
        await self.db.flush()
        return note

    async def list_notes(self, encounter_id: uuid.UUID) -> Sequence[EncounterNote]:
        stmt = select(EncounterNote).where(EncounterNote.encounter_id == encounter_id).order_by(EncounterNote.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()
