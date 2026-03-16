from fastapi import APIRouter

from app.core.encounters.encounters.router import router as encounters_router
from app.core.encounters.diagnoses.router import router as diagnoses_router
from app.core.encounters.notes.router import router as notes_router
from app.core.encounters.timeline.router import router as timeline_router
from app.core.encounters.clinical_flags.router import router as flags_router

router = APIRouter()

router.include_router(encounters_router)
router.include_router(diagnoses_router)
router.include_router(notes_router)
router.include_router(timeline_router)
router.include_router(flags_router)
