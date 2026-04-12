from fastapi import APIRouter
from app.dependencies import DBSession

router = APIRouter(prefix="/telemedicine", tags=["Patient Portal - Telemedicine"])

@router.get("/sessions")
async def get_sessions(db: DBSession, patient_id: str):
    return []
