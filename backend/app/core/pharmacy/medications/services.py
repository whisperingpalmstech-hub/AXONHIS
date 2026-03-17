import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from .models import Medication
from .schemas import MedicationCreate

class MedicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_medication(self, data: MedicationCreate) -> Medication:
        med = Medication(**data.model_dump())
        self.db.add(med)
        try:
            await self.db.flush()
        except IntegrityError:
            raise HTTPException(status_code=400, detail="Medication code already exists")
        return med

    async def get_medication(self, med_id: uuid.UUID) -> Medication:
        res = await self.db.execute(select(Medication).where(Medication.id == med_id))
        med = res.scalar_one_or_none()
        if not med:
            raise HTTPException(status_code=404, detail="Medication not found")
        return med

    async def list_medications(self, limit: int = 100) -> list[Medication]:
        res = await self.db.execute(select(Medication).limit(limit))
        return list(res.scalars().all())
