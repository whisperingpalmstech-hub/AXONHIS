import uuid
from fastapi import APIRouter, status, HTTPException
from app.core.encounters.encounters.schemas import EncounterCreate, EncounterUpdate, EncounterOut
from app.core.encounters.encounters.services import EncounterService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/encounters", tags=["encounters"])

@router.post("/", response_model=EncounterOut, status_code=status.HTTP_201_CREATED)
async def create_encounter(data: EncounterCreate, db: DBSession, user: CurrentUser):
    return await EncounterService(db, user).create_encounter(data, user.id)

@router.get("/", response_model=list[EncounterOut])
async def list_encounters(db: DBSession, user: CurrentUser, skip: int = 0, limit: int = 20):
    return await EncounterService(db, user).list_encounters(skip, limit)

@router.get("/{encounter_id}", response_model=EncounterOut)
async def get_encounter(encounter_id: uuid.UUID, db: DBSession, user: CurrentUser):
    encounter = await EncounterService(db, user).get_encounter_by_id(encounter_id)
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return encounter

@router.put("/{encounter_id}", response_model=EncounterOut)
async def update_encounter(encounter_id: uuid.UUID, data: EncounterUpdate, db: DBSession, user: CurrentUser):
    service = EncounterService(db, user)
    encounter = await service.get_encounter_by_id(encounter_id)
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return await service.update_encounter(encounter, data, user.id)
