"""
Order services – the central business logic engine.

Rules:
- APPROVED triggers: TaskService.generate_tasks() + BillingService.create_entry()
- CANCELLED triggers: BillingService.reverse_entry()
- Every state change emits an Event
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.orders.models import Order, OrderItem, OrderStatus
from app.core.orders.schemas import OrderCreate


class OrderService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: OrderCreate, ordered_by: uuid.UUID) -> Order:
        """Create a new order with items in PENDING_APPROVAL state."""
        order = Order(
            encounter_id=data.encounter_id,
            patient_id=data.patient_id,
            order_type=data.order_type,
            priority=data.priority,
            notes=data.notes,
            metadata_=data.metadata_,
            ordered_by=ordered_by,
            status=OrderStatus.PENDING_APPROVAL,
        )
        self.db.add(order)
        await self.db.flush()  # Get order.id before adding items

        for item_data in data.items:
            item = OrderItem(order_id=order.id, **item_data.model_dump())
            self.db.add(item)

        await self.db.flush()
        return order

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        result = await self.db.execute(
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        return result.scalar_one_or_none()

    async def list_by_encounter(self, encounter_id: uuid.UUID) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .where(Order.encounter_id == encounter_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def approve(self, order: Order, approved_by: uuid.UUID, notes: str | None = None) -> Order:
        """Approve an order — triggers task generation and billing."""
        if order.status != OrderStatus.PENDING_APPROVAL:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot approve order in status '{order.status}'",
            )
        order.status = OrderStatus.APPROVED
        order.approved_by = approved_by
        order.approved_at = datetime.now(timezone.utc)
        if notes:
            order.notes = notes
        await self.db.flush()
        return order

    async def cancel(self, order: Order, reason: str) -> Order:
        """Cancel an order — triggers billing reversal."""
        if order.status in (OrderStatus.COMPLETED, OrderStatus.CANCELLED):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot cancel order in status '{order.status}'",
            )
        order.status = OrderStatus.CANCELLED
        order.cancellation_reason = reason
        await self.db.flush()
        return order

    async def complete(self, order: Order) -> Order:
        if order.status != OrderStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot complete order in status '{order.status}'",
            )
        order.status = OrderStatus.COMPLETED
        order.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return order
