import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import SurgeryNote
from .schemas import SurgeryNoteCreate, SurgeryNoteUpdate
from app.core.ot.workflow.services import OTWorkflowService


class SurgeryNoteService:
    @staticmethod
    async def create_note(db: AsyncSession, note_in: SurgeryNoteCreate) -> SurgeryNote:
        note = SurgeryNote(**note_in.model_dump())
        db.add(note)
        await db.commit()
        await db.refresh(note)

        # Log in timeline
        await OTWorkflowService.log_timeline_event(
            db, note.schedule_id, "note_added", f"Surgery note added: {note.note_type}", note.created_by
        )

        return note

    @staticmethod
    async def update_note(db: AsyncSession, note_id: uuid.UUID, note_in: SurgeryNoteUpdate) -> SurgeryNote | None:
        note = await db.get(SurgeryNote, note_id)
        if not note:
            return None
        
        update_data = note_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(note, field, value)
        
        await db.commit()
        await db.refresh(note)
        return note

    @staticmethod
    async def get_notes_for_schedule(db: AsyncSession, schedule_id: uuid.UUID) -> list[SurgeryNote]:
        stmt = select(SurgeryNote).where(SurgeryNote.schedule_id == schedule_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())
