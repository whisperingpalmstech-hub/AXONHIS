"""OT Module — API Routes. Linked to IPD, billing, pharmacy."""
import uuid
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import CurrentUser
from .schemas import *
from .services import *

router = APIRouter(prefix="/ot-enhanced", tags=["OT Enhanced"])

@router.get("/dashboard", response_model=OTDashboardStats)
async def ot_dashboard(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await OTDashboardService(db).get_stats(user.org_id)

# Rooms
@router.get("/rooms", response_model=List[OTRoomOut])
async def list_ot_rooms(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await OTRoomService(db).list_rooms(user.org_id)

@router.post("/rooms", response_model=OTRoomOut)
async def create_ot_room(data: OTRoomCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await OTRoomService(db).create(data, user.org_id)

@router.put("/rooms/{room_id}/status", response_model=OTRoomOut)
async def update_room_status(room_id: uuid.UUID, status: str, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await OTRoomService(db).update_status(room_id, status, user.org_id)

# Schedules
@router.get("/schedules", response_model=List[OTScheduleOut])
async def list_schedules(user: CurrentUser, status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    return await OTScheduleService(db).list_schedules(user.org_id, status=status)

@router.post("/schedules", response_model=OTScheduleOut)
async def create_schedule(data: OTScheduleCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await OTScheduleService(db).create(data, user.id, user.org_id)

@router.get("/schedules/{schedule_id}", response_model=OTScheduleOut)
async def get_schedule(schedule_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await OTScheduleService(db).get(schedule_id, user.org_id)

@router.put("/schedules/{schedule_id}/status", response_model=OTScheduleOut)
async def update_schedule_status(schedule_id: uuid.UUID, data: OTStatusUpdate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await OTScheduleService(db).update_status(schedule_id, data, user.org_id)

# Consumables
@router.post("/consumables", response_model=OTConsumableOut)
async def add_consumable(data: OTConsumableCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await OTConsumableService(db).add(data, user.org_id)

@router.get("/consumables/{schedule_id}", response_model=List[OTConsumableOut])
async def list_consumables(schedule_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await OTConsumableService(db).list_consumables(schedule_id, user.org_id)

# Anesthesia
@router.post("/anesthesia", response_model=OTAnesthesiaOut)
async def create_anesthesia_record(data: OTAnesthesiaCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    name = getattr(user, 'full_name', None) or getattr(user, 'email', 'Staff')
    return await OTAnesthesiaService(db).create(data, user.id, str(name), user.org_id)

@router.get("/anesthesia/{schedule_id}", response_model=OTAnesthesiaOut)
async def get_anesthesia(schedule_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    r = await OTAnesthesiaService(db).get(schedule_id, user.org_id)
    if not r: raise HTTPException(404, "No anesthesia record")
    return r
