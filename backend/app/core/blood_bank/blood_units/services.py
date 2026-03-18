from uuid import UUID
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import BloodUnit, BloodUnitStatus
from .schemas import BloodUnitCreate, BloodUnitUpdate


class BloodUnitService:
    @staticmethod
    async def create_unit(session: AsyncSession, unit_in: BloodUnitCreate) -> BloodUnit:
        stmt = select(BloodUnit).where(BloodUnit.unit_id == unit_in.unit_id)
        existing = await session.scalar(stmt)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Blood unit already exists")

        db_unit = BloodUnit(**unit_in.model_dump())

        # Check if expired at creation
        if db_unit.expiry_date < datetime.now(timezone.utc):
            db_unit.status = BloodUnitStatus.EXPIRED

        session.add(db_unit)
        await session.commit()
        await session.refresh(db_unit)
        return db_unit

    @staticmethod
    async def get_unit(session: AsyncSession, unit_id: UUID) -> BloodUnit:
        db_unit = await session.get(BloodUnit, unit_id)
        if not db_unit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blood unit not found")
        return db_unit

    @staticmethod
    async def list_units(session: AsyncSession, status: str | None = None) -> list[BloodUnit]:
        stmt = select(BloodUnit)
        if status:
            stmt = stmt.where(BloodUnit.status == status)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_unit(session: AsyncSession, unit_id: UUID, unit_in: BloodUnitUpdate) -> BloodUnit:
        db_unit = await BloodUnitService.get_unit(session, unit_id)
        update_data = unit_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_unit, key, value)
        await session.commit()
        await session.refresh(db_unit)
        return db_unit
