import uuid
from fastapi import APIRouter, HTTPException, status
from .schemas import SurgeryNoteCreate, SurgeryNoteUpdate, SurgeryNoteOut
from .services import SurgeryNoteService
from app.dependencies import CurrentUser, DBSession


router = APIRouter(prefix="/note", tags=["Surgery Notes"])

@router.post("/", response_model=SurgeryNoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(data: SurgeryNoteCreate, db: DBSession, user: CurrentUser) -> SurgeryNoteOut:
    if not data.created_by:
        data.created_by = user.id
    return await SurgeryNoteService.create_note(db, data)

@router.get("/{schedule_id}", response_model=list[SurgeryNoteOut])
async def list_notes_for_schedule(schedule_id: uuid.UUID, db: DBSession, _: CurrentUser) -> list[SurgeryNoteOut]:
    return await SurgeryNoteService.get_notes_for_schedule(db, schedule_id)

@router.put("/{note_id}", response_model=SurgeryNoteOut)
async def update_note(note_id: uuid.UUID, data: SurgeryNoteUpdate, db: DBSession, _: CurrentUser) -> SurgeryNoteOut:
    note = await SurgeryNoteService.update_note(db, note_id, data)
    if not note:
        raise HTTPException(status_code=404, detail="Surgery note not found")
    return note
