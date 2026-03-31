from fastapi import APIRouter, Depends, HTTPException, status
from app.core.auth.models import User
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.wards.services import WardService
from app.core.wards.schemas import WardCreate, WardOut, RoomCreate, RoomOut, BedCreate, BedOut, BedAssignmentCreate, BedAssignmentOut, BedTransferCreate, BedTransferOut
from typing import List

from app.dependencies import get_current_user_optional, CurrentUser

router = APIRouter(prefix="/wards", tags=["Wards & Bed Management"])

# ════════ WARD ENDPOINTS ════════
@router.post("/", response_model=WardOut)
async def create_ward(ward: WardCreate, db: AsyncSession = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    if current_user and current_user.org_id:
        ward.org_id = current_user.org_id
    return await WardService.create_ward(db, ward)

@router.get("/", response_model=List[WardOut])
async def list_wards(db: AsyncSession = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    from app.core.wards.models import Ward
    query = select(Ward)
    if current_user and current_user.org_id:
        query = query.where(Ward.org_id == current_user.org_id)
    result = await db.execute(query)
    return result.scalars().all()

# ════════ ROOM ENDPOINTS ════════
@router.post("/rooms", response_model=RoomOut)
async def create_room(room: RoomCreate, db: AsyncSession = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    if current_user and current_user.org_id:
        room.org_id = current_user.org_id
    return await WardService.create_room(db, room)

# ════════ BED ENDPOINTS ════════
@router.post("/beds", response_model=BedOut)
async def create_bed(bed: BedCreate, db: AsyncSession = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    if current_user and current_user.org_id:
        bed.org_id = current_user.org_id
    return await WardService.create_bed(db, bed)

@router.get("/beds", response_model=List[BedOut])
async def list_beds(db: AsyncSession = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    from app.core.wards.models import Bed
    query = select(Bed)
    if current_user and current_user.org_id:
        query = query.where(Bed.org_id == current_user.org_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/assign", response_model=BedAssignmentOut)
async def assign_bed(assignment: BedAssignmentCreate, db: AsyncSession = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    if current_user and current_user.org_id:
        assignment.org_id = current_user.org_id
    return await WardService.assign_bed(db, assignment)

@router.post("/transfer", response_model=BedTransferOut)
async def transfer_bed(transfer: BedTransferCreate, db: AsyncSession = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    if current_user and current_user.org_id:
        transfer.org_id = current_user.org_id
    return await WardService.transfer_bed(db, transfer)

@router.post("/release")
async def release_bed(patient_id: str, encounter_id: str, db: AsyncSession = Depends(get_db)):
    res = await WardService.release_bed(db, patient_id, encounter_id)
    if not res:
        raise HTTPException(status_code=404, detail="Active assignment not found")
    return {"message": "Bed released and marked for cleaning"}

@router.post("/cleaning/complete")
async def complete_cleaning(bed_id: str, user_id: str, db: AsyncSession = Depends(get_db)):
    return await WardService.complete_cleaning(db, bed_id, user_id)

@router.get("/{ward_id}/rooms", response_model=List[RoomOut])
async def list_ward_rooms(ward_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    from app.core.wards.models import Room
    query = select(Room).filter(Room.ward_id == ward_id)
    if current_user and current_user.org_id:
        query = query.where(Room.org_id == current_user.org_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/rooms/{room_id}/beds", response_model=List[BedOut])
async def list_room_beds(room_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    from app.core.wards.models import Bed
    query = select(Bed).filter(Bed.room_id == room_id)
    if current_user and current_user.org_id:
        query = query.where(Bed.org_id == current_user.org_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/beds/bulk")
async def create_beds_bulk(beds: List[BedCreate], db: AsyncSession = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    created = []
    for bed in beds:
        if current_user and current_user.org_id:
            bed.org_id = current_user.org_id
        res = await WardService.create_bed(db, bed)
        created.append(res)
    return {"status": "success", "count": len(created)}

@router.get("/dashboard/occupancy")
async def occupancy_stats(db: AsyncSession = Depends(get_db), current_user: User | None = Depends(get_current_user_optional)):
    return await WardService.get_occupancy_stats(db, current_user.org_id if current_user else None)
