import uuid
from fastapi import APIRouter, HTTPException, status
from .schemas import SurgicalTeamCreate, SurgicalTeamUpdate, SurgicalTeamOut
from .services import SurgicalTeamService
from app.dependencies import CurrentUser, DBSession


router = APIRouter(prefix="/team", tags=["Surgical Teams"])

@router.post("/", response_model=SurgicalTeamOut, status_code=status.HTTP_201_CREATED)
async def assign_team(data: SurgicalTeamCreate, db: DBSession, _: CurrentUser) -> SurgicalTeamOut:
    try:
        return await SurgicalTeamService.assign_team(db, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{schedule_id}", response_model=SurgicalTeamOut)
async def get_team(schedule_id: uuid.UUID, db: DBSession, _: CurrentUser) -> SurgicalTeamOut:
    team = await SurgicalTeamService.get_team(db, schedule_id)
    if not team:
        raise HTTPException(status_code=404, detail="Surgical team not found for this schedule")
    return team

@router.put("/{schedule_id}", response_model=SurgicalTeamOut)
async def update_team(schedule_id: uuid.UUID, data: SurgicalTeamUpdate, db: DBSession, _: CurrentUser) -> SurgicalTeamOut:
    team = await SurgicalTeamService.update_team(db, schedule_id, data)
    if not team:
        raise HTTPException(status_code=404, detail="Surgical team not found for this schedule")
    return team
