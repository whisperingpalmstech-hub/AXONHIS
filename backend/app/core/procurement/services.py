from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException
import uuid
import random
import string

from app.core.inventory.models import InventoryItem, BatchRecord
from app.core.auth.models import User
from app.core.notifications.services import NotificationService

from .models import VendorMaster, PurchaseRequest, PurchaseRequestItem, PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, GRNItem
from .schemas import VendorMasterCreate, PurchaseRequestCreate, PurchaseOrderCreate, GRNCreate, GRNInspectionCommand
from app.core.inventory.models import Store, InventoryItem

def generate_number(prefix: str) -> str:
    rnd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{rnd}"

class ProcurementService:
    # --- VENDORS ---
    @staticmethod
    async def get_vendors(db: AsyncSession):
        res = await db.execute(select(VendorMaster))
        return list(res.scalars().all())

    @staticmethod
    async def create_vendor(db: AsyncSession, data: VendorMasterCreate):
        v = VendorMaster(**data.model_dump())
        db.add(v)
        await db.commit()
        await db.refresh(v)
        return v

    @staticmethod
    async def get_stores(db: AsyncSession):
        res = await db.execute(select(Store))
        return list(res.scalars().all())

    @staticmethod
    async def get_items(db: AsyncSession):
        res = await db.execute(select(InventoryItem))
        return list(res.scalars().all())

    # --- PURCHASE REQUESTS ---
    @staticmethod
    async def get_prs(db: AsyncSession):
        res = await db.execute(select(PurchaseRequest).options(joinedload(PurchaseRequest.items)))
        return list(res.unique().scalars().all())

    @staticmethod
    async def create_pr(db: AsyncSession, data: PurchaseRequestCreate, user_id: uuid.UUID):
        pr = PurchaseRequest(
            pr_number=generate_number("PR"),
            requesting_store_id=data.requesting_store_id,
            delivery_store_id=data.delivery_store_id,
            priority=data.priority,
            justification=data.justification,
            created_by=user_id
        )
        db.add(pr)
        await db.flush()
        
        for it in data.items:
            pi = PurchaseRequestItem(pr_id=pr.id, **it.model_dump())
            db.add(pi)
            
        await db.commit()
        await db.refresh(pr)
        return await ProcurementService.get_pr(db, pr.id)

    @staticmethod
    async def get_pr(db: AsyncSession, pr_id: uuid.UUID):
        res = await db.execute(select(PurchaseRequest).options(joinedload(PurchaseRequest.items)).where(PurchaseRequest.id == pr_id))
        return res.unique().scalars().first()

    @staticmethod
    async def approve_pr(db: AsyncSession, pr_id: uuid.UUID):
        pr = await ProcurementService.get_pr(db, pr_id)
        if not pr: raise HTTPException(status_code=404)
        pr.status = "APPROVED"
        for item in pr.items:
            item.approved_qty = item.requested_qty
        await db.commit()
        
        # Connect to ROOT: Notify Store Manager
        sys_admin = (await db.execute(select(User).limit(1))).scalars().first()
        if sys_admin:
            ns = NotificationService(db)
            await ns.send(user_id=sys_admin.id, title="PR Approved", message=f"Purchase Request {pr.pr_number} has been approved and moved to sourcing.", notification_type="SUCCESS", link="/dashboard/procurement")

        return pr

    # --- PURCHASE ORDERS ---
    @staticmethod
    async def get_pos(db: AsyncSession):
        res = await db.execute(select(PurchaseOrder).options(joinedload(PurchaseOrder.items)))
        return list(res.unique().scalars().all())
        
    @staticmethod
    async def create_po(db: AsyncSession, data: PurchaseOrderCreate, user_id: uuid.UUID):
        gross_amt = sum(float(i.ordered_qty) * float(i.rate) for i in data.items)
        tax_amt = sum(float(i.ordered_qty) * float(i.rate) * float(i.tax_pct) / 100 for i in data.items)
        net_amt = gross_amt + tax_amt
        
        po = PurchaseOrder(
            po_number=generate_number("PO"),
            vendor_id=data.vendor_id,
            pr_id=data.pr_id,
            quotation_id=data.quotation_id,
            total_amount=gross_amt,
            tax_amount=tax_amt,
            net_amount=net_amt,
            delivery_date=data.delivery_date,
            warranty_terms=data.warranty_terms,
            created_by=user_id,
            status="SENT"
        )
        db.add(po)
        await db.flush()

        # Connect to ROOT: Notify that PO was sent to Sourcing
        sys_admin = (await db.execute(select(User).limit(1))).scalars().first()
        if sys_admin:
            ns = NotificationService(db)
            await ns.send(user_id=sys_admin.id, title="Purchase Order Generated", message=f"PO {po.po_number} has been generated.", notification_type="INFO", link="/dashboard/procurement")
        
        for it in data.items:
            pi = PurchaseOrderItem(po_id=po.id, **it.model_dump())
            db.add(pi)
            
        if data.pr_id:
            pr = await ProcurementService.get_pr(db, data.pr_id)
            if pr: pr.status = "PO_GENERATED"
            
        await db.commit()
        res = await db.execute(select(PurchaseOrder).options(joinedload(PurchaseOrder.items)).where(PurchaseOrder.id == po.id))
        return res.unique().scalars().first()

    # --- GRN & INVENTORY INTEGRATION ---
    @staticmethod
    async def get_grns(db: AsyncSession):
        res = await db.execute(select(GoodsReceiptNote).options(joinedload(GoodsReceiptNote.items)))
        return list(res.unique().scalars().all())

    @staticmethod
    async def create_grn(db: AsyncSession, data: GRNCreate, user_id: uuid.UUID):
        grn = GoodsReceiptNote(
            grn_number=generate_number("GRN"),
            po_id=data.po_id,
            vendor_id=data.vendor_id,
            store_id=data.store_id,
            invoice_number=data.invoice_number,
            challan_number=data.challan_number,
            received_by=user_id
        )
        db.add(grn)
        await db.flush()
        
        po_res = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == data.po_id))
        po = po_res.scalars().first()
        if po:
            po.status = "PARTIAL_GRN"
            
        sys_admin = (await db.execute(select(User).limit(1))).scalars().first()
        if sys_admin:
            ns = NotificationService(db)
            await ns.send(user_id=sys_admin.id, title="Delivery Arrived", message=f"GRN {grn.grn_number} registered. Pending Physical Inspection.", notification_type="WARNING", link="/dashboard/procurement")
        
        for it in data.items:
            gi = GRNItem(grn_id=grn.id, **it.model_dump())
            db.add(gi)
            
        await db.commit()
        res = await db.execute(select(GoodsReceiptNote).options(joinedload(GoodsReceiptNote.items)).where(GoodsReceiptNote.id == grn.id))
        return res.unique().scalars().first()

    @staticmethod
    async def inspect_and_sync_grn(db: AsyncSession, grn_id: uuid.UUID, item_inspections: dict):
        res = await db.execute(select(GoodsReceiptNote).options(joinedload(GoodsReceiptNote.items)).where(GoodsReceiptNote.id == grn_id))
        grn = res.unique().scalars().first()
        if not grn: raise HTTPException(status_code=404)
        
        # Loop and accept/reject physically
        all_ok = True
        for item in grn.items:
            insp = item_inspections.get(str(item.id))
            if insp:
                item.accepted_qty = insp.accepted_qty
                item.rejected_qty = insp.rejected_qty
                item.inspection_remarks = insp.inspection_remarks
                
                # INTEGRATION WITH ROOT INVENTORY!
                if item.accepted_qty > 0:
                    batch = BatchRecord(
                        store_id=grn.store_id,
                        item_id=item.item_id,
                        batch_number=item.batch_number or generate_number("BT"),
                        expiry_date=item.expiry_date,
                        quantity=item.accepted_qty,
                        purchase_price=0.0 # From PO rate theoretically
                    )
                    db.add(batch)
            if item.rejected_qty > 0:
                all_ok = False
                
        grn.status = "APPROVED" if all_ok else "PARTIAL_REJECTION"
        
        po_res = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == grn.po_id))
        po = po_res.scalars().first()
        if po:
            po.status = "FULL_GRN"
            
        await db.commit()
        
        sys_admin = (await db.execute(select(User).limit(1))).scalars().first()
        if sys_admin:
            ns = NotificationService(db)
            await ns.send(user_id=sys_admin.id, title="GRN Inspected & Inventory Synced", message=f"GRN {grn.grn_number} physically inspected. Stock added to store.", notification_type="SUCCESS", link="/dashboard/procurement")

        return grn
