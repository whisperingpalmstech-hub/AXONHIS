import uuid
from fastapi import APIRouter, status
from app.core.encounters.notes.schemas import EncounterNoteCreate, EncounterNoteOut
from app.core.encounters.notes.services import NoteService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/encounters/{encounter_id}/notes", tags=["encounters-notes"])

@router.post("/", response_model=EncounterNoteOut, status_code=status.HTTP_201_CREATED)
async def add_note(encounter_id: uuid.UUID, data: EncounterNoteCreate, db: DBSession, user: CurrentUser):
    return await NoteService(db).add_note(encounter_id, user.id, data, org_id=user.org_id)

@router.get("/", response_model=list[EncounterNoteOut])
async def list_notes(encounter_id: uuid.UUID, db: DBSession, _: CurrentUser):
    return await NoteService(db).list_notes(encounter_id)
