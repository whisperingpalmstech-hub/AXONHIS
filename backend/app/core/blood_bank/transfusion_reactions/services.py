from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import TransfusionReaction
from .schemas import TransfusionReactionCreate, TransfusionReactionUpdate


class TransfusionReactionService:
    @staticmethod
    async def create_reaction(session: AsyncSession, reaction_in: TransfusionReactionCreate) -> TransfusionReaction:
        db_reaction = TransfusionReaction(**reaction_in.model_dump())
        session.add(db_reaction)
        await session.commit()
        await session.refresh(db_reaction)
        return db_reaction

    @staticmethod
    async def get_reaction(session: AsyncSession, reaction_id: UUID) -> TransfusionReaction:
        db_reaction = await session.get(TransfusionReaction, reaction_id)
        if not db_reaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reaction not found")
        return db_reaction

    @staticmethod
    async def list_reactions(session: AsyncSession) -> list[TransfusionReaction]:
        result = await session.execute(select(TransfusionReaction))
        return list(result.scalars().all())

    @staticmethod
    async def update_reaction(session: AsyncSession, reaction_id: UUID, reaction_in: TransfusionReactionUpdate) -> TransfusionReaction:
        db_reaction = await TransfusionReactionService.get_reaction(session, reaction_id)
        update_data = reaction_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_reaction, key, value)
        await session.commit()
        await session.refresh(db_reaction)
        return db_reaction
