from uuid import UUID
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Transfusion, TransfusionStatus
from .schemas import TransfusionCreate, TransfusionUpdate


class TransfusionService:
    @staticmethod
    async def create_transfusion(session: AsyncSession, transfusion_in: TransfusionCreate) -> Transfusion:
        db_transfusion = Transfusion(**transfusion_in.model_dump())
        session.add(db_transfusion)
        await session.commit()
        await session.refresh(db_transfusion)
        return db_transfusion

    @staticmethod
    async def get_transfusion(session: AsyncSession, transfusion_id: UUID) -> Transfusion:
        db_transfusion = await session.get(Transfusion, transfusion_id)
        if not db_transfusion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfusion not found")
        return db_transfusion

    @staticmethod
    async def list_transfusions(session: AsyncSession) -> list[Transfusion]:
        result = await session.execute(select(Transfusion))
        return list(result.scalars().all())

    @staticmethod
    async def update_transfusion(session: AsyncSession, transfusion_id: UUID, transfusion_in: TransfusionUpdate) -> Transfusion:
        db_transfusion = await TransfusionService.get_transfusion(session, transfusion_id)
        update_data = transfusion_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_transfusion, key, value)
        await session.commit()
        await session.refresh(db_transfusion)
        return db_transfusion
