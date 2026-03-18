from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import BloodStorageUnit
from .schemas import BloodStorageUnitCreate, BloodStorageUnitUpdate


class BloodInventoryService:
    @staticmethod
    async def create_storage_unit(session: AsyncSession, storage_in: BloodStorageUnitCreate) -> BloodStorageUnit:
        stmt = select(BloodStorageUnit).where(BloodStorageUnit.storage_name == storage_in.storage_name)
        existing = await session.scalar(stmt)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Storage unit already exists")

        db_storage = BloodStorageUnit(**storage_in.model_dump())
        session.add(db_storage)
        await session.commit()
        await session.refresh(db_storage)
        return db_storage

    @staticmethod
    async def get_storage_unit(session: AsyncSession, storage_id: UUID) -> BloodStorageUnit:
        db_storage = await session.get(BloodStorageUnit, storage_id)
        if not db_storage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage unit not found")
        return db_storage

    @staticmethod
    async def list_storage_units(session: AsyncSession) -> list[BloodStorageUnit]:
        result = await session.execute(select(BloodStorageUnit))
        return list(result.scalars().all())

    @staticmethod
    async def update_storage_unit(session: AsyncSession, storage_id: UUID, storage_in: BloodStorageUnitUpdate) -> BloodStorageUnit:
        db_storage = await BloodInventoryService.get_storage_unit(session, storage_id)
        update_data = storage_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_storage, key, value)
        await session.commit()
        await session.refresh(db_storage)
        return db_storage

    @staticmethod
    async def delete_storage_unit(session: AsyncSession, storage_id: UUID) -> None:
        db_storage = await BloodInventoryService.get_storage_unit(session, storage_id)
        await session.delete(db_storage)
        await session.commit()
