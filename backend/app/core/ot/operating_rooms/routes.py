import uuid
from fastapi import APIRouter, HTTPException, status
from .schemas import OperatingRoomCreate, OperatingRoomUpdate, OperatingRoomOut
from .services import OperatingRoomService
from app.dependencies import CurrentUser, DBSession


router = APIRouter(prefix="/rooms", tags=["Operating Rooms"])

@router.post("/", response_model=OperatingRoomOut, status_code=status.HTTP_201_CREATED)
async def create_room(data: OperatingRoomCreate, db: DBSession, _: CurrentUser) -> OperatingRoomOut:
    return await OperatingRoomService.create_room(db, data)

@router.get("/", response_model=list[OperatingRoomOut])
async def list_rooms(db: DBSession, _: CurrentUser) -> list[OperatingRoomOut]:
    return await OperatingRoomService.get_all_rooms(db)

@router.get("/{room_id}", response_model=OperatingRoomOut)
async def get_room(room_id: uuid.UUID, db: DBSession, _: CurrentUser) -> OperatingRoomOut:
    room = await OperatingRoomService.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Operating room not found")
    return room

@router.put("/{room_id}", response_model=OperatingRoomOut)
async def update_room(room_id: uuid.UUID, data: OperatingRoomUpdate, db: DBSession, _: CurrentUser) -> OperatingRoomOut:
    room = await OperatingRoomService.update_room(db, room_id, data)
    if not room:
        raise HTTPException(status_code=404, detail="Operating room not found")
    return room

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(room_id: uuid.UUID, db: DBSession, _: CurrentUser):
    if not await OperatingRoomService.delete_room(db, room_id):
        raise HTTPException(status_code=404, detail="Operating room not found")
