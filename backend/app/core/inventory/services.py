from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, timezone

from .models import Store, InvItem, BatchRecord, StockLedger, StoreIndent, StoreIndentItem, MaterialIssue, MaterialIssueItem
from .schemas import StoreBase, ItemBase, OpeningBalance, IndentCreate, IssueCreate

class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_store(self, data: StoreBase):
        # Check if store already exists by name
        res = await self.db.execute(select(Store).where(Store.name == data.name))
        existing = res.scalars().first()
        if existing:
            return existing
            
        store = Store(name=data.name, store_type=data.store_type, parent_store_id=data.parent_store_id)
        self.db.add(store)
        await self.db.commit()
        await self.db.refresh(store)
        return store

    async def create_item(self, data: ItemBase):
        # Check if item exists
        res = await self.db.execute(select(InvItem).where(InvItem.item_code == data.item_code))
        existing = res.scalars().first()
        if existing:
            return existing
            
        item = InvItem(item_code=data.item_code, name=data.name, category=data.category, uom=data.uom)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_stores(self):
        res = await self.db.execute(select(Store))
        return res.scalars().all()

    async def get_items(self):
        res = await self.db.execute(select(InvItem))
        return res.scalars().all()

    async def get_stock_levels(self, store_id: Optional[uuid.UUID] = None):
        """Aggregate total stock per item across all batches in a store."""
        query = select(
            InvItem.name,
            InvItem.item_code,
            InvItem.category,
            InvItem.uom,
            func.sum(BatchRecord.quantity).label('total_quantity')
        ).join(BatchRecord, InvItem.id == BatchRecord.item_id).group_by(InvItem.id)
        
        if store_id:
            query = query.filter(BatchRecord.store_id == store_id)
            
        res = await self.db.execute(query)
        return list(res.mappings().all())

    async def get_stock_movements(self, limit: int = 50):
        """Fetch recent transactions from the stock ledger."""
        query = select(StockLedger).options(
            selectinload(StockLedger.item)
        ).order_by(StockLedger.transaction_date.desc()).limit(limit)
        
        res = await self.db.execute(query)
        movements = []
        for m in res.scalars().all():
            movements.append({
                "id": str(m.id),
                "date": m.transaction_date,
                "item_name": m.item.name,
                "type": m.transaction_type,
                "quantity": float(m.quantity_change),
                "balance": float(m.closing_balance)
            })
        return movements

    async def get_expiry_alerts(self, days: int = 90):
        """Items expiring within the specified timeframe."""
        limit_date = datetime.now(timezone.utc) + timedelta(days=days)
        query = select(BatchRecord, InvItem).join(
            InvItem, BatchRecord.item_id == InvItem.id
        ).where(BatchRecord.expiry_date <= limit_date, BatchRecord.quantity > 0)
        
        res = await self.db.execute(query)
        alerts = []
        for batch, item in res.all():
            alerts.append({
                "item_name": item.name,
                "batch_number": batch.batch_number,
                "expiry_date": batch.expiry_date,
                "quantity": float(batch.quantity)
            })
        return alerts


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

    async def get_indents(self):
        query = select(StoreIndent).options(
            selectinload(StoreIndent.requesting_store),
            selectinload(StoreIndent.issuing_store),
            selectinload(StoreIndent.items).selectinload(StoreIndentItem.item)
        ).order_by(StoreIndent.created_at.desc())
        res = await self.db.execute(query)
        return res.scalars().all()

    async def get_issues(self):
        query = select(MaterialIssue).options(
            selectinload(MaterialIssue.issuing_store),
            selectinload(MaterialIssue.receiving_store)
        ).order_by(MaterialIssue.issued_at.desc())
        res = await self.db.execute(query)
        return res.scalars().all()

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
            
    async def approve_indent(self, indent_id: uuid.UUID):
        from .models import StoreIndent
        indent = await self.db.get(StoreIndent, indent_id)
        if not indent or indent.status != "DRAFT":
            raise HTTPException(status_code=400, detail="Only draft indents can be approved")
        
        indent.status = "APPROVED"
        await self.db.commit()
        await self.db.refresh(indent)
        return indent

    async def get_gate_passes(self):
        from .models import GatePass
        from sqlalchemy.orm import selectinload
        res = await self.db.execute(
            select(GatePass).options(
                selectinload(GatePass.issue)
            )
        )
        return res.scalars().all()

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
            batch = None
            if itm.batch_record_id:
                batch = await self.db.get(BatchRecord, itm.batch_record_id)
            
            # If batch is missing, invalid, or belongs to another store, try to auto-pick
            if not batch or batch.quantity < itm.issued_quantity or batch.store_id != data.issuing_store_id:
                res = await self.db.execute(
                    select(BatchRecord).where(
                        BatchRecord.item_id == itm.item_id,
                        BatchRecord.store_id == data.issuing_store_id,
                        BatchRecord.quantity >= itm.issued_quantity
                    ).order_by(BatchRecord.expiry_date.asc())
                )
                batch = res.scalars().first()
                
            if not batch:
                raise HTTPException(status_code=400, detail="Insufficient stock in issuing store for this item.")

            # Deduct from issuing store
            from decimal import Decimal
            batch.quantity -= Decimal(str(itm.issued_quantity))
            
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
                batch_record_id=batch.id,
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
            
        # Update original indent if exists
        if issue.indent_id:
            from .models import StoreIndent
            indent = await self.db.get(StoreIndent, issue.indent_id)
            if indent:
                indent.status = "RECEIVED"
        
        issue.status = "COMPLETED"
        await self.db.commit()
        return {"message": "Material received and stock updated", "status": "COMPLETED"}

    async def process_adjustment(self, data: 'PhysicalAdjustment', user_id: uuid.UUID):
        from .schemas import PhysicalAdjustment
        from decimal import Decimal
        
        # Calculate current total quantity
        res = await self.db.execute(select(func.coalesce(func.sum(BatchRecord.quantity), 0)).where(BatchRecord.item_id == data.item_id, BatchRecord.store_id == data.store_id))
        current_qty = float(res.scalar() or 0)
        
        diff = data.physical_quantity - current_qty
        if diff == 0:
            return {"message": "No adjustment needed", "status": "UNCHANGED"}
            
        # Apply diff to batches and establish the batch to associate
        selected_batch_id = None
        if diff > 0:
            batch = BatchRecord(
                store_id=data.store_id,
                item_id=data.item_id,
                batch_number="ADJ-" + datetime.now().strftime("%Y%m%d%H%M"),
                expiry_date=datetime.now(timezone.utc) + timedelta(days=365),
                quantity=Decimal(str(diff)),
                purchase_price=Decimal("0.0")
            )
            self.db.add(batch)
            await self.db.flush()
            selected_batch_id = batch.id
        else:
            query = select(BatchRecord).where(
                BatchRecord.item_id == data.item_id,
                BatchRecord.store_id == data.store_id,
                BatchRecord.quantity > 0
            ).order_by(BatchRecord.expiry_date.asc())
            
            batches = (await self.db.execute(query)).scalars().all()
            remaining_to_deduct = Decimal(str(abs(diff)))
            for b in batches:
                if selected_batch_id is None:
                    selected_batch_id = b.id
                if remaining_to_deduct <= 0:
                    break
                deduct = min(Decimal(str(b.quantity)), remaining_to_deduct)
                b.quantity = Decimal(str(b.quantity)) - deduct
                remaining_to_deduct -= deduct
                
        # Write to ledger
        adj_ledger = StockLedger(
            item_id=data.item_id,
            store_id=data.store_id,
            batch_record_id=selected_batch_id or uuid.uuid4(),  # Fallback if no batch found
            transaction_type="ADJ",
            reference_id=data.reason[:50],
            quantity_change=Decimal(str(diff)),
            closing_balance=Decimal(str(data.physical_quantity)),
            performed_by=user_id
        )
        self.db.add(adj_ledger)
        
        await self.db.commit()
        return {"message": "Physical adjustment log processed successfully", "status": "COMPLETED"}

    async def get_ledger_history(self, item_id: uuid.UUID, store_id: Optional[uuid.UUID] = None):
        query = select(StockLedger).where(StockLedger.item_id == item_id)
        if store_id:
            query = query.where(StockLedger.store_id == store_id)
        
        query = query.order_by(StockLedger.transaction_date.desc())
        res = await self.db.execute(query)
        return res.scalars().all()

    async def get_inventory_analytics(self):
        from sqlalchemy import select, func
        from .models import InvItem, BatchRecord, StockLedger
        
        # 1. Fetch consolidated inventory with total value
        items_res = await self.db.execute(
            select(
                InvItem, 
                func.coalesce(func.sum(BatchRecord.quantity), 0).label('total_qty'),
                func.coalesce(func.sum(BatchRecord.quantity * BatchRecord.purchase_price), 0).label('total_value')
            )
            .outerjoin(BatchRecord, InvItem.id == BatchRecord.item_id)
            .group_by(InvItem.id)
        )
        
        inventory_data = items_res.fetchall()
        
        # 2. Calculate ABC Analysis (Value Based)
        total_portfolio_value = sum([float(r.total_value) for r in inventory_data])
        sorted_inventory = sorted(inventory_data, key=lambda x: float(x.total_value), reverse=True)
        
        abc_analysis = []
        cumulative_value = 0
        for r in sorted_inventory:
            val = float(r.total_value)
            prev_pct = cumulative_value / total_portfolio_value if total_portfolio_value > 0 else 0
            
            cumulative_value += val
            
            if prev_pct < 0.7:
                abc_class = "A"
            elif prev_pct < 0.9:
                abc_class = "B"
            else:
                abc_class = "C"
                
            individual_pct = (val / total_portfolio_value) if total_portfolio_value > 0 else 0
                
            abc_analysis.append({
                "item_id": r.InvItem.id,
                "name": r.InvItem.name,
                "value": val,
                "abc_class": abc_class,
                "percentage": round(individual_pct * 100, 2)
            })
            
        # 3. Generate Auto-PO Reorder Alerts
        reorder_alerts = []
        for r in inventory_data:
            if float(r.total_qty) < 50: # Trigger threshold 
                reorder_alerts.append({
                    "item_id": r.InvItem.id,
                    "name": r.InvItem.name,
                    "current_qty": float(r.total_qty),
                    "reorder_level": 50,
                    "action": "AUTO_PO_DRAFTED"
                })
                
        # 4. Identify Dead Stock (Inactive > 90 Days)
        dead_stock = []
        ledger_res = await self.db.execute(
            select(StockLedger.item_id, func.max(StockLedger.transaction_date).label('latest_txn'))
            .group_by(StockLedger.item_id)
        )
        last_txns = {str(row.item_id): row.latest_txn for row in ledger_res.fetchall()}
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        for r in inventory_data:
            qty = float(r.total_qty)
            if qty > 0:
                last_txn_date = last_txns.get(str(r.InvItem.id))
                days_inactive = (now - last_txn_date).days if last_txn_date else 999
                
                if days_inactive > 90:
                    dead_stock.append({
                        "item_id": r.InvItem.id,
                        "name": r.InvItem.name,
                        "quantity": qty,
                        "value": float(r.total_value),
                        "days_inactive": days_inactive if days_inactive != 999 else "Never"
                    })

        return {
            "abc_analysis": abc_analysis,
            "reorder_alerts": reorder_alerts,
            "dead_stock": dead_stock
        }
