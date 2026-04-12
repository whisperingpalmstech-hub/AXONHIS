import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import AnesthesiaRecord
from .schemas import AnesthesiaRecordCreate, AnesthesiaRecordUpdate


class AnesthesiaRecordService:
    @staticmethod
    async def create_record(db: AsyncSession, record_in: AnesthesiaRecordCreate) -> AnesthesiaRecord:
        record = AnesthesiaRecord(**record_in.model_dump())
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def update_record(db: AsyncSession, schedule_id: uuid.UUID, record_in: AnesthesiaRecordUpdate) -> AnesthesiaRecord | None:
        stmt = select(AnesthesiaRecord).where(AnesthesiaRecord.schedule_id == schedule_id)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        
        update_data = record_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)
        
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def get_record(db: AsyncSession, schedule_id: uuid.UUID) -> AnesthesiaRecord | None:
        stmt = select(AnesthesiaRecord).where(AnesthesiaRecord.schedule_id == schedule_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
