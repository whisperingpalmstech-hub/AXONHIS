from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import BloodComponent
from .schemas import BloodComponentCreate, BloodComponentUpdate


class BloodComponentService:
    @staticmethod
    async def create_component(session: AsyncSession, component_in: BloodComponentCreate) -> BloodComponent:
        stmt = select(BloodComponent).where(BloodComponent.component_name == component_in.component_name)
        existing = await session.execute(stmt)
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Component already exists")

        db_comp = BloodComponent(**component_in.model_dump())
        session.add(db_comp)
        await session.commit()
        await session.refresh(db_comp)
        return db_comp

    @staticmethod
    async def get_component(session: AsyncSession, component_id: UUID) -> BloodComponent:
        db_comp = await session.get(BloodComponent, component_id)
        if not db_comp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found")
        return db_comp

    @staticmethod
    async def list_components(session: AsyncSession) -> list[BloodComponent]:
        result = await session.execute(select(BloodComponent))
        return list(result.scalars().all())

    @staticmethod
    async def update_component(session: AsyncSession, component_id: UUID, component_in: BloodComponentUpdate) -> BloodComponent:
        db_comp = await BloodComponentService.get_component(session, component_id)
        update_data = component_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_comp, key, value)
        await session.commit()
        await session.refresh(db_comp)
        return db_comp

    @staticmethod
    async def delete_component(session: AsyncSession, component_id: UUID) -> None:
        db_comp = await BloodComponentService.get_component(session, component_id)
        await session.delete(db_comp)
        await session.commit()
