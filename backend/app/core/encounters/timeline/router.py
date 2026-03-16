import uuid
from fastapi import APIRouter
from app.core.encounters.timeline.schemas import EncounterTimelineOut
from app.core.encounters.timeline.services import TimelineService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/encounters/{encounter_id}/timeline", tags=["encounters-timeline"])

@router.get("/", response_model=list[EncounterTimelineOut])
async def get_timeline(encounter_id: uuid.UUID, db: DBSession, _: CurrentUser):
    return await TimelineService(db).get_timeline(encounter_id)
