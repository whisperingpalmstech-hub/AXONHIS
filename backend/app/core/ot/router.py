from fastapi import APIRouter
from app.core.ot.operating_rooms.routes import router as rooms_router
from app.core.ot.surgery_schedule.routes import router as schedule_router
from app.core.ot.surgical_procedures.routes import router as procedures_router
from app.core.ot.surgical_teams.routes import router as team_router
from app.core.ot.anesthesia_records.routes import router as anesthesia_router
from app.core.ot.surgery_events.routes import router as events_router
from app.core.ot.surgery_notes.routes import router as notes_router
from app.core.ot.dashboard.routes import router as dashboard_router

router = APIRouter(prefix="/ot", tags=["Operating Theatre"])

router.include_router(rooms_router)
router.include_router(schedule_router)
router.include_router(procedures_router)
router.include_router(team_router)
router.include_router(anesthesia_router)
router.include_router(events_router)
router.include_router(notes_router)
router.include_router(dashboard_router)
