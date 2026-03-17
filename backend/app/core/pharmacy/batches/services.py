import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from .models import DrugBatch
from .schemas import DrugBatchCreate

class BatchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_batch(self, data: DrugBatchCreate) -> DrugBatch:
        batch = DrugBatch(**data.model_dump())
        self.db.add(batch)
        await self.db.flush()
        return batch

    async def list_batches(self, limit: int = 100) -> list[DrugBatch]:
        res = await self.db.execute(select(DrugBatch).limit(limit))
        return list(res.scalars().all())

    async def get_near_expiry_batches(self, days: int = 30) -> list[DrugBatch]:
        from datetime import date, timedelta
        target_date = date.today() + timedelta(days=days)
        res = await self.db.execute(
            select(DrugBatch).where(DrugBatch.expiry_date <= target_date)
        )
        return list(res.scalars().all())
