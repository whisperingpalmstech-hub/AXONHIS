import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import ImagingSchedule
from .schemas import ImagingScheduleCreate
from app.core.radiology.imaging_orders.models import ImagingOrder, ImagingOrderStatus

class ImagingScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def schedule_scan(self, data: ImagingScheduleCreate, user_id: uuid.UUID) -> ImagingSchedule:
        # Update order status to SCHEDULED
        res = await self.db.execute(select(ImagingOrder).where(ImagingOrder.id == data.imaging_order_id))
        order = res.scalar_one_or_none()
        if order:
            order.status = ImagingOrderStatus.SCHEDULED
        
        schedule = ImagingSchedule(
            **data.model_dump(),
            scheduled_by=user_id
        )
        self.db.add(schedule)
        await self.db.flush()
        return schedule

    async def get_schedule_by_order_id(self, imaging_order_id: uuid.UUID) -> ImagingSchedule:
        result = await self.db.execute(select(ImagingSchedule).where(ImagingSchedule.imaging_order_id == imaging_order_id))
        return result.scalar_one_or_none()
