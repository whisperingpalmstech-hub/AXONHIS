from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
import uuid

from .models import Store, InventoryItem, BatchRecord, StockLedger, StoreIndent, StoreIndentItem, MaterialIssue, MaterialIssueItem
from .schemas import StoreBase, ItemBase, OpeningBalance, IndentCreate, IssueCreate

class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_store(self, data: StoreBase):
        store = Store(name=data.name, store_type=data.store_type, parent_store_id=data.parent_store_id)
        self.db.add(store)
        await self.db.commit()
        await self.db.refresh(store)
        return store

    async def create_item(self, data: ItemBase):
        item = InventoryItem(item_code=data.item_code, name=data.name, category=data.category, uom=data.uom)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_stores(self):
        res = await self.db.execute(select(Store))
        return res.scalars().all()

    async def add_opening_balance(self, data: OpeningBalance, user_id: uuid.UUID):
        # Create Batch Record
        batch = BatchRecord(
            store_id=data.store_id,
            item_id=data.item_id,
            batch_number=data.batch_number,
            expiry_date=data.expiry_date,
            quantity=data.quantity,
            purchase_price=data.purchase_price
        )
        self.db.add(batch)
        await self.db.flush()

        # Create Ledger Entry
        ledger = StockLedger(
            store_id=data.store_id,
            item_id=data.item_id,
            batch_record_id=batch.id,
            transaction_type='OPENING_BALANCE',
            quantity_change=data.quantity,
            closing_balance=data.quantity,
            performed_by=user_id
        )
        self.db.add(ledger)
        await self.db.commit()
        return batch

    async def create_indent(self, data: IndentCreate, user_id: uuid.UUID):
        indent = StoreIndent(
            indent_number=f"IND-{uuid.uuid4().hex[:6].upper()}",
            requesting_store_id=data.requesting_store_id,
            issuing_store_id=data.issuing_store_id,
            justification=data.justification,
            created_by=user_id
        )
        self.db.add(indent)
        await self.db.flush()

        for itm in data.items:
            req_item = StoreIndentItem(
                indent_id=indent.id,
                item_id=itm.item_id,
                requested_quantity=itm.requested_quantity
            )
            self.db.add(req_item)
            
        await self.db.commit()
        await self.db.refresh(indent)
        return indent

    async def create_issue(self, data: IssueCreate, user_id: uuid.UUID):
        issue = MaterialIssue(
            issue_number=f"ISS-{uuid.uuid4().hex[:6].upper()}",
            indent_id=data.indent_id,
            issuing_store_id=data.issuing_store_id,
            receiving_store_id=data.receiving_store_id,
            issued_by=user_id
        )
        self.db.add(issue)
        await self.db.flush()

        for itm in data.items:
            # check available batch
            batch = await self.db.get(BatchRecord, itm.batch_record_id)
            if not batch or batch.quantity < itm.issued_quantity or batch.store_id != data.issuing_store_id:
                raise HTTPException(status_code=400, detail="Insufficient stock in batch")

            # Deduct from issuing store
            batch.quantity -= itm.issued_quantity
            
            # Log deduction
            ledger_out = StockLedger(
                store_id=data.issuing_store_id,
                item_id=itm.item_id,
                batch_record_id=batch.id,
                transaction_type='ISSUE',
                quantity_change=-itm.issued_quantity,
                closing_balance=batch.quantity,
                reference_id=str(issue.id),
                performed_by=user_id
            )
            self.db.add(ledger_out)

            iss_itm = MaterialIssueItem(
                issue_id=issue.id,
                item_id=itm.item_id,
                batch_record_id=itm.batch_record_id,
                issued_quantity=itm.issued_quantity
            )
            self.db.add(iss_itm)

        if data.indent_id:
            ind = await self.db.get(StoreIndent, data.indent_id)
            if ind:
                ind.status = "ISSUED"

        await self.db.commit()
        await self.db.refresh(issue)
        return issue

    async def accept_issue(self, issue_id: uuid.UUID, user_id: uuid.UUID):
        issue = await self.db.get(MaterialIssue, issue_id)
        if not issue or issue.status != "PENDING_ACCEPTANCE":
            raise HTTPException(status_code=400, detail="Invalid issue to accept")
        
        issue.status = "ACCEPTED"
        
        res = await self.db.execute(select(MaterialIssueItem).where(MaterialIssueItem.issue_id == issue_id))
        issue_items = res.scalars().all()
        
        for itm in issue_items:
            itm.accepted_quantity = itm.issued_quantity
            # Find original batch to copy details
            orig_batch = await self.db.get(BatchRecord, itm.batch_record_id)
            
            # Find or create batch record in receiving store
            batch_query = await self.db.execute(
                select(BatchRecord).where(
                    BatchRecord.store_id == issue.receiving_store_id,
                    BatchRecord.item_id == itm.item_id,
                    BatchRecord.batch_number == orig_batch.batch_number
                )
            )
            recv_batch = batch_query.scalars().first()
            if not recv_batch:
                recv_batch = BatchRecord(
                    store_id=issue.receiving_store_id,
                    item_id=itm.item_id,
                    batch_number=orig_batch.batch_number,
                    expiry_date=orig_batch.expiry_date,
                    quantity=itm.accepted_quantity,
                    purchase_price=orig_batch.purchase_price
                )
                self.db.add(recv_batch)
                await self.db.flush()
            else:
                recv_batch.quantity += itm.accepted_quantity
            
            # Ledger IN for receiving store
            ledger_in = StockLedger(
                store_id=issue.receiving_store_id,
                item_id=itm.item_id,
                batch_record_id=recv_batch.id,
                transaction_type='RECEIPT',
                quantity_change=itm.accepted_quantity,
                closing_balance=recv_batch.quantity,
                reference_id=str(issue.id),
                performed_by=user_id
            )
            self.db.add(ledger_in)
            
        await self.db.commit()
        return {"message": "Material received and stock updated"}
