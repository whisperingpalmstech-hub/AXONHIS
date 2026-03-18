from uuid import UUID
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import TransfusionOrder, BloodAllocation, AllocationStatus
from .schemas import TransfusionOrderCreate, TransfusionOrderUpdate, BloodAllocationCreate, BloodAllocationUpdate
from ..blood_units.models import BloodUnit, BloodUnitStatus
from ..blood_units.services import BloodUnitService


class TransfusionOrderService:
    @staticmethod
    async def create_order(session: AsyncSession, order_in: TransfusionOrderCreate) -> TransfusionOrder:
        db_order = TransfusionOrder(**order_in.model_dump())
        session.add(db_order)
        await session.commit()
        await session.refresh(db_order)
        return db_order

    @staticmethod
    async def get_order(session: AsyncSession, order_id: UUID) -> TransfusionOrder:
        db_order = await session.get(TransfusionOrder, order_id)
        if not db_order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfusion order not found")
        return db_order

    @staticmethod
    async def list_orders(session: AsyncSession) -> list[TransfusionOrder]:
        result = await session.execute(select(TransfusionOrder))
        return list(result.scalars().all())

    @staticmethod
    async def update_order(session: AsyncSession, order_id: UUID, order_in: TransfusionOrderUpdate) -> TransfusionOrder:
        db_order = await TransfusionOrderService.get_order(session, order_id)
        update_data = order_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_order, key, value)
        await session.commit()
        await session.refresh(db_order)
        return db_order

    @staticmethod
    async def allocate_unit(session: AsyncSession, allocation_in: BloodAllocationCreate) -> BloodAllocation:
        # Verify order exists
        order = await TransfusionOrderService.get_order(session, allocation_in.transfusion_order_id)

        # Verify unit exists and is available
        unit = await BloodUnitService.get_unit(session, allocation_in.blood_unit_id)
        if unit.status != BloodUnitStatus.AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Blood unit {unit.unit_id} is not available (current status: {unit.status})"
            )
        
        # Here we should verify crossmatch is compatible or it was already checked?
        # That check should run before allocation (see routes/workflow).

        db_allocation = BloodAllocation(**allocation_in.model_dump())
        session.add(db_allocation)

        # Update unit status to reserved
        unit.status = BloodUnitStatus.RESERVED

        await session.commit()
        await session.refresh(db_allocation)
        return db_allocation

    @staticmethod
    async def update_allocation_status(session: AsyncSession, allocation_id: UUID, allocation_in: BloodAllocationUpdate) -> BloodAllocation:
        db_allocation = await session.get(BloodAllocation, allocation_id)
        if not db_allocation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")
        
        if allocation_in.allocation_status == AllocationStatus.ISSUED:
            unit = await BloodUnitService.get_unit(session, db_allocation.blood_unit_id)
            unit.status = BloodUnitStatus.ISSUED

        if allocation_in.allocation_status == AllocationStatus.RETURNED:
            unit = await BloodUnitService.get_unit(session, db_allocation.blood_unit_id)
            unit.status = BloodUnitStatus.AVAILABLE

        db_allocation.allocation_status = allocation_in.allocation_status
        await session.commit()
        await session.refresh(db_allocation)
        return db_allocation
