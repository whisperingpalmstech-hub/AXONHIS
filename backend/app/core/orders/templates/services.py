"""Services for order templates and order sets."""
import uuid
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.orders.templates.models import OrderTemplate, OrderTemplateItem, OrderSet, OrderSetItem
from app.core.orders.templates.schemas import OrderTemplateCreate, OrderSetCreate


class OrderTemplateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: OrderTemplateCreate, created_by: uuid.UUID) -> OrderTemplate:
        template = OrderTemplate(
            template_name=data.template_name,
            description=data.description,
            order_type=data.order_type,
            is_public=data.is_public,
            created_by=created_by,
        )
        self.db.add(template)
        await self.db.flush()

        for item_data in data.items:
            item = OrderTemplateItem(template_id=template.id, **item_data.model_dump())
            self.db.add(item)
        await self.db.flush()

        return await self.get_by_id(template.id)

    async def get_by_id(self, template_id: uuid.UUID) -> OrderTemplate | None:
        result = await self.db.execute(
            select(OrderTemplate)
            .where(OrderTemplate.id == template_id)
            .options(selectinload(OrderTemplate.items))
        )
        return result.scalar_one_or_none()

    async def list_all(self, user_id: uuid.UUID | None = None) -> list[OrderTemplate]:
        stmt = (
            select(OrderTemplate)
            .options(selectinload(OrderTemplate.items))
            .order_by(OrderTemplate.template_name)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())

    async def search(self, query: str) -> list[OrderTemplate]:
        stmt = (
            select(OrderTemplate)
            .where(OrderTemplate.template_name.ilike(f"%{query}%"))
            .options(selectinload(OrderTemplate.items))
            .limit(20)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())


class OrderSetService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: OrderSetCreate, created_by: uuid.UUID) -> OrderSet:
        order_set = OrderSet(
            set_name=data.set_name,
            description=data.description,
            clinical_context=data.clinical_context,
            is_public=data.is_public,
            created_by=created_by,
        )
        self.db.add(order_set)
        await self.db.flush()

        for item_data in data.items:
            item = OrderSetItem(set_id=order_set.id, **item_data.model_dump())
            self.db.add(item)
        await self.db.flush()

        return await self.get_by_id(order_set.id)

    async def get_by_id(self, set_id: uuid.UUID) -> OrderSet | None:
        result = await self.db.execute(
            select(OrderSet)
            .where(OrderSet.id == set_id)
            .options(selectinload(OrderSet.items))
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[OrderSet]:
        stmt = (
            select(OrderSet)
            .options(selectinload(OrderSet.items))
            .order_by(OrderSet.set_name)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())
