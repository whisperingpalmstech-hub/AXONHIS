import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from .models import InventoryItem, ControlledDrugLog
from .schemas import InventoryItemCreate, InventoryItemUpdate

class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_inventory_item(self, data: InventoryItemCreate) -> InventoryItem:
        res = await self.db.execute(select(InventoryItem).where(InventoryItem.drug_id == data.drug_id))
        if res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Inventory item for this drug already exists")
            
        item = InventoryItem(**data.model_dump())
        self.db.add(item)
        await self.db.flush()
        return item

    async def update_inventory(self, drug_id: uuid.UUID, data: InventoryItemUpdate, user_id: uuid.UUID) -> InventoryItem:
        res = await self.db.execute(select(InventoryItem).where(InventoryItem.drug_id == drug_id))
        item = res.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        diff = data.quantity_available - float(item.quantity_available)
        item.quantity_available = data.quantity_available
        from datetime import datetime, timezone
        item.last_updated = datetime.now(timezone.utc)

        # Log controlled drug change (we'll just log all manually here for simplicity)
        log = ControlledDrugLog(
            drug_id=drug_id,
            transaction_type=data.reason,
            quantity=diff,
            performed_by=user_id
        )
        self.db.add(item)
        self.db.add(log)
        await self.db.flush()
        return item

    async def get_inventory(self, limit: int = 100) -> list[InventoryItem]:
        res = await self.db.execute(select(InventoryItem).limit(limit))
        return list(res.scalars().all())

    async def get_low_stock(self) -> list[InventoryItem]:
        from sqlalchemy import literal_column
        res = await self.db.execute(
            select(InventoryItem).where(InventoryItem.quantity_available <= InventoryItem.reorder_threshold)
        )
        return list(res.scalars().all())
