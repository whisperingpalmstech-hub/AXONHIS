from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from .schemas import (
    TransfusionOrderCreate, TransfusionOrderUpdate, TransfusionOrderResponse,
    BloodAllocationCreate, BloodAllocationUpdate, BloodAllocationResponse
)
from .services import TransfusionOrderService

router = APIRouter()

@router.post("", response_model=TransfusionOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: TransfusionOrderCreate,
    session: AsyncSession = Depends(get_db),
):
    return await TransfusionOrderService.create_order(session, order_in)

@router.get("", response_model=list[TransfusionOrderResponse])
async def list_orders(
    session: AsyncSession = Depends(get_db),
):
    return await TransfusionOrderService.list_orders(session)

@router.get("/{order_id}", response_model=TransfusionOrderResponse)
async def get_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    return await TransfusionOrderService.get_order(session, order_id)

@router.patch("/{order_id}", response_model=TransfusionOrderResponse)
async def update_order(
    order_id: UUID,
    order_in: TransfusionOrderUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await TransfusionOrderService.update_order(session, order_id, order_in)

@router.post("/{order_id}/allocations", response_model=BloodAllocationResponse, status_code=status.HTTP_201_CREATED)
async def allocate_unit(
    order_id: UUID,
    allocation_in: BloodAllocationCreate,
    session: AsyncSession = Depends(get_db),
):
    if allocation_in.transfusion_order_id != order_id:
        allocation_in.transfusion_order_id = order_id
    return await TransfusionOrderService.allocate_unit(session, allocation_in)

@router.patch("/{order_id}/allocations/{allocation_id}", response_model=BloodAllocationResponse)
async def update_allocation(
    order_id: UUID,
    allocation_id: UUID,
    allocation_in: BloodAllocationUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await TransfusionOrderService.update_allocation_status(session, allocation_id, allocation_in)
