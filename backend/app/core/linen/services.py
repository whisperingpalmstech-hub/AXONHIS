from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.core.linen.models import (
    LinenCategory, LinenInventoryLedger, LaundryBatch,
    LinenTransaction, TransactionType
)
from app.core.linen.schemas import (
    LinenCategoryCreate, LaundryBatchCreate,
    LinenTransactionCreate, LaundryBatchStatusUpdate
)

class LinenService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_category(self, data: LinenCategoryCreate, org_id: uuid.UUID) -> LinenCategory:
        category = LinenCategory(**data.model_dump(), org_id=org_id)
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def get_categories(self, org_id: uuid.UUID) -> List[LinenCategory]:
        result = await self.db.execute(select(LinenCategory).where(LinenCategory.org_id == org_id))
        return list(result.scalars().all())

    async def _update_ledger(self, category_id: uuid.UUID, department: str, org_id: uuid.UUID, 
                             clean_delta: int = 0, dirty_delta: int = 0, in_wash_delta: int = 0):
        # Fetch or create ledger
        result = await self.db.execute(
            select(LinenInventoryLedger)
            .where((LinenInventoryLedger.category_id == category_id) & 
                   (LinenInventoryLedger.department_id == department) &
                   (LinenInventoryLedger.org_id == org_id))
        )
        ledger = result.scalar_one_or_none()
        
        if not ledger:
            ledger = LinenInventoryLedger(
                category_id=category_id,
                department_id=department,
                org_id=org_id,
                clean_quantity=0,
                dirty_quantity=0,
                in_wash_quantity=0
            )
            self.db.add(ledger)
            
        ledger.clean_quantity += clean_delta
        ledger.dirty_quantity += dirty_delta
        ledger.in_wash_quantity += in_wash_delta

        if ledger.clean_quantity < 0 or ledger.dirty_quantity < 0 or ledger.in_wash_quantity < 0:
            raise HTTPException(status_code=400, detail=f"Insufficient stock in {department} for category {category_id}")

    async def log_transaction(self, data: LinenTransactionCreate, user_id: uuid.UUID, org_id: uuid.UUID) -> LinenTransaction:
        tx = LinenTransaction(**data.model_dump(), performed_by=user_id, org_id=org_id)
        self.db.add(tx)
        
        # Update ledgers based on transaction type
        t_type = tx.transaction_type
        
        if t_type == TransactionType.NEW_STOCK:
            await self._update_ledger(tx.category_id, tx.destination_department, org_id, clean_delta=tx.quantity)
            
        elif t_type == TransactionType.ISSUE_TO_WARD:
            if tx.source_department == "LAUNDRY-MAIN":
                await self._update_ledger(tx.category_id, tx.source_department, org_id, clean_delta=-tx.quantity)
            await self._update_ledger(tx.category_id, tx.destination_department, org_id, clean_delta=tx.quantity)
            
        elif t_type == TransactionType.COLLECT_FROM_WARD:
            # Mark ward clean as dirty (subtracted implicitly by usage, but tracked explicitly here as collected)
            await self._update_ledger(tx.category_id, tx.source_department, org_id, clean_delta=-tx.quantity)
            # Add to destination (e.g., LAUNDRY-DIRTY)
            if tx.destination_department:
                await self._update_ledger(tx.category_id, tx.destination_department, org_id, dirty_delta=tx.quantity)
                
        elif t_type == TransactionType.SEND_TO_LAUNDRY:
            await self._update_ledger(tx.category_id, tx.source_department, org_id, dirty_delta=-tx.quantity)
            await self._update_ledger(tx.category_id, "LAUNDRY-MAIN", org_id, in_wash_delta=tx.quantity)
            
        elif t_type == TransactionType.RECEIVE_FROM_LAUNDRY:
            await self._update_ledger(tx.category_id, "LAUNDRY-MAIN", org_id, in_wash_delta=-tx.quantity, clean_delta=tx.quantity)
            
        elif t_type == TransactionType.CONDEMN:
            await self._update_ledger(tx.category_id, tx.source_department, org_id, clean_delta=-tx.quantity)

        await self.db.commit()
        await self.db.refresh(tx)
        
        # Load relationship
        await self.db.refresh(tx, ['category'])
        return tx

    async def create_batch(self, data: LaundryBatchCreate, operator_id: uuid.UUID, org_id: uuid.UUID) -> LaundryBatch:
        batch = LaundryBatch(**data.model_dump(), operator_id=operator_id, org_id=org_id)
        self.db.add(batch)
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def get_batches(self, org_id: uuid.UUID) -> List[LaundryBatch]:
        result = await self.db.execute(select(LaundryBatch).where(LaundryBatch.org_id == org_id).order_by(LaundryBatch.start_time.desc()))
        return list(result.scalars().all())

    async def update_batch_status(self, batch_id: uuid.UUID, data: LaundryBatchStatusUpdate, org_id: uuid.UUID) -> LaundryBatch:
        result = await self.db.execute(select(LaundryBatch).where(LaundryBatch.id == batch_id, LaundryBatch.org_id == org_id))
        batch = result.scalar_one_or_none()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
            
        batch.status = data.status
        if data.end_time:
            batch.end_time = data.end_time
            
        await self.db.commit()
        await self.db.refresh(batch)
        return batch

    async def get_ledger(self, department: Optional[str], org_id: uuid.UUID) -> List[LinenInventoryLedger]:
        query = select(LinenInventoryLedger).where(LinenInventoryLedger.org_id == org_id)
        if department:
            query = query.where(LinenInventoryLedger.department_id == department)
        result = await self.db.execute(query)
        ledgers = list(result.scalars().all())
        for l in ledgers:
            await self.db.refresh(l, ['category'])
        return ledgers
