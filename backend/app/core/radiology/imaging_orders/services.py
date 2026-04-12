import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import ImagingOrder, ImagingOrderStatus
from .schemas import ImagingOrderCreate

class ImagingOrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(self, data: ImagingOrderCreate, user_id: uuid.UUID) -> ImagingOrder:
        order = ImagingOrder(
            **data.model_dump(),
            status=ImagingOrderStatus.PENDING,
            ordered_by=user_id
        )
        self.db.add(order)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_order_by_id(self, order_id: uuid.UUID) -> ImagingOrder:
        result = await self.db.execute(select(ImagingOrder).where(ImagingOrder.id == order_id))
        return result.scalar_one_or_none()

    async def list_orders(self, skip: int = 0, limit: int = 100):
        result = await self.db.execute(select(ImagingOrder).offset(skip).limit(limit))
        return result.scalars().all()

    async def update_order_status(self, order_id: uuid.UUID, new_status: str) -> ImagingOrder:
        order = await self.get_order_by_id(order_id)
        if order:
            order.status = new_status
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(order)
        return order
