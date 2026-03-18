import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import OperatingRoom, OperatingRoomStatus
from .schemas import OperatingRoomCreate, OperatingRoomUpdate


class OperatingRoomService:
    @staticmethod
    async def create_room(db: AsyncSession, room_in: OperatingRoomCreate) -> OperatingRoom:
        room = OperatingRoom(**room_in.model_dump())
        db.add(room)
        await db.commit()
        await db.refresh(room)
        return room

    @staticmethod
    async def get_room(db: AsyncSession, room_id: uuid.UUID) -> OperatingRoom | None:
        return await db.get(OperatingRoom, room_id)

    @staticmethod
    async def get_all_rooms(db: AsyncSession) -> list[OperatingRoom]:
        result = await db.execute(select(OperatingRoom))
        return list(result.scalars().all())

    @staticmethod
    async def update_room(db: AsyncSession, room_id: uuid.UUID, room_in: OperatingRoomUpdate) -> OperatingRoom | None:
        room = await db.get(OperatingRoom, room_id)
        if not room:
            return None
        
        update_data = room_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(room, field, value)
        
        await db.commit()
        await db.refresh(room)
        return room

    @staticmethod
    async def delete_room(db: AsyncSession, room_id: uuid.UUID) -> bool:
        room = await db.get(OperatingRoom, room_id)
        if not room:
            return False
        await db.delete(room)
        await db.commit()
        return True
