import asyncio
import uuid
from app.database import engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.inventory.models import Store, InventoryItem
from app.core.procurement.models import VendorMaster, PurchaseRequest, PurchaseRequestItem, PurchaseOrder, PurchaseOrderItem
from app.core.auth.models import User

async def seed():
    async with AsyncSession(engine) as db:
        # Check stores
        res = await db.execute(select(Store).where(Store.store_type == "MAIN"))
        main_store = res.scalars().first()
        res = await db.execute(select(Store).where(Store.store_type == "PHARMACY"))
        pharmacy_store = res.scalars().first()
        
        # Check user
        admin = (await db.execute(select(User).limit(1))).scalars().first()
        
        if not main_store or not pharmacy_store or not admin:
            print("Missing stores or admin. Seeding basic stores...")
            if not main_store:
                main_store = Store(name="Main Central Store", store_type="MAIN")
                db.add(main_store)
            if not pharmacy_store:
                pharmacy_store = Store(name="Pharmacy Store", store_type="PHARMACY")
                db.add(pharmacy_store)
            await db.flush()

        # Seed realistic items
        item_data = [
            {"item_code": "MED010", "name": "Paracetamol 500mg Tablet", "category": "MEDICATION", "uom": "Strip"},
            {"item_code": "CON055", "name": "Nitrile Examination Gloves", "category": "CONSUMABLE", "uom": "Box"},
            {"item_code": "RX092", "name": "Ceftriaxone 1g Injection", "category": "MEDICATION", "uom": "Vial"},
            {"item_code": "EQ033", "name": "BP Cuff - Adult", "category": "EQUIPMENT", "uom": "Each"}
        ]
        
        real_items = []
        for idata in item_data:
            res = await db.execute(select(InventoryItem).where(InventoryItem.item_code == idata["item_code"]))
            it = res.scalars().first()
            if not it:
                it = InventoryItem(**idata)
                db.add(it)
                await db.flush()
            real_items.append(it)
            
        # Seed Vendors
        ven1 = (await db.execute(select(VendorMaster).where(VendorMaster.vendor_code == "VND-1001"))).scalars().first()
        if not ven1:
            ven1 = VendorMaster(vendor_code="VND-1001", name="Global MedTech Suppliers", contact_person="Alicia Vance", is_active=True)
            db.add(ven1)
            
        ven2 = (await db.execute(select(VendorMaster).where(VendorMaster.vendor_code == "VND-1002"))).scalars().first()
        if not ven2:
            ven2 = VendorMaster(vendor_code="VND-1002", name="Pinnacle Pharma Distributors", contact_person="John Smith", is_active=True)
            db.add(ven2)
            
        await db.flush()
        
        # Seed PRs
        existing_pr = (await db.execute(select(PurchaseRequest))).scalars().first()
        if not existing_pr:
            pr1 = PurchaseRequest(
                pr_number="PR-XJ90T",
                requesting_store_id=pharmacy_store.id,
                delivery_store_id=main_store.id,
                priority="URGENT",
                justification="Stock depletion due to outbreak. Raising urgent indent.",
                status="PENDING_APPROVAL",
                created_by=admin.id if admin else None
            )
            db.add(pr1)
            await db.flush()
            
            db.add(PurchaseRequestItem(pr_id=pr1.id, item_id=real_items[0].id, requested_qty=5000))
            db.add(PurchaseRequestItem(pr_id=pr1.id, item_id=real_items[2].id, requested_qty=1000))
            
            pr2 = PurchaseRequest(
                pr_number="PR-MM22P",
                requesting_store_id=main_store.id,
                delivery_store_id=main_store.id,
                priority="NORMAL",
                justification="Quarterly operational restock.",
                status="APPROVED",
                created_by=admin.id if admin else None
            )
            db.add(pr2)
            await db.flush()
            
            db.add(PurchaseRequestItem(pr_id=pr2.id, item_id=real_items[1].id, requested_qty=200, approved_qty=200))

            po1 = PurchaseOrder(
                po_number="PO-Z88M2",
                vendor_id=ven1.id,
                pr_id=pr2.id,
                total_amount=2500.0,
                tax_amount=125.0,
                net_amount=2625.0,
                status="SENT",
                created_by=admin.id if admin else None
            )
            db.add(po1)
            await db.flush()
            db.add(PurchaseOrderItem(po_id=po1.id, item_id=real_items[1].id, ordered_qty=200, rate=12.5, tax_pct=5.0))

            print("Real dataset injected successfully.")
        else:
            print("Data already exists.")
            
        await db.commit()

if __name__ == "__main__":
    asyncio.run(seed())
