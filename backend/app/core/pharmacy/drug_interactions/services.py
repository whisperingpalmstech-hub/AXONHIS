import uuid
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from .models import DrugInteraction
from .schemas import DrugInteractionCreate

class DrugInteractionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_interaction(self, data: DrugInteractionCreate) -> DrugInteraction:
        interaction = DrugInteraction(**data.model_dump())
        self.db.add(interaction)
        await self.db.flush()
        return interaction

    async def check_interactions(self, drug_ids: list[uuid.UUID]) -> list[DrugInteraction]:
        if len(drug_ids) < 2:
            return []
            
        res = await self.db.execute(
            select(DrugInteraction)
            .where(
                or_(
                    and_(DrugInteraction.drug_a_id.in_(drug_ids), DrugInteraction.drug_b_id.in_(drug_ids)),
                )
            )
        )
        return list(res.scalars().all())

    async def list_interactions(self, limit: int = 100) -> list[DrugInteraction]:
        res = await self.db.execute(select(DrugInteraction).limit(limit))
        return list(res.scalars().all())
