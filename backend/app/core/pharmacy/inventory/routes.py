import uuid
from fastapi import APIRouter, Query, Depends
from app.dependencies import DBSession, CurrentUser
from .schemas import InventoryItemCreate, InventoryItemUpdate, InventoryItemOut
from .services import InventoryService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(tags=["pharmacy-inventory"])

@router.get("/inventory/search")
async def search_inventory(query: str = Query(""), db: AsyncSession = Depends(get_db)):
    """Search medications with stock info for pharmacy sales."""
    from app.core.pharmacy.medications.models import Medication
    from app.core.pharmacy.inventory.models import InventoryItem
    from app.core.pharmacy.batches.models import DrugBatch

    q = select(Medication)
    if query:
        q = q.where(
            Medication.drug_name.ilike(f"%{query}%") |
            Medication.generic_name.ilike(f"%{query}%") |
            Medication.drug_code.ilike(f"%{query}%")
        )
    q = q.limit(20)
    res = await db.execute(q)
    meds = res.scalars().all()

    results = []
    for med in meds:
        inv_q = select(InventoryItem).where(InventoryItem.drug_id == med.id)
        inv_res = await db.execute(inv_q)
        inv = inv_res.scalar_one_or_none()

        batch_q = select(DrugBatch).where(DrugBatch.drug_id == med.id).limit(1)
        batch_res = await db.execute(batch_q)
        batch = batch_res.scalar_one_or_none()

        results.append({
            "id": str(med.id),
            "drug_id": str(med.id),
            "drug_name": med.drug_name,
            "generic_name": med.generic_name,
            "drug_code": med.drug_code,
            "strength": med.strength,
            "form": med.form,
            "manufacturer": med.manufacturer,
            "quantity_available": float(inv.quantity_available) if inv else 0,
            "unit_price": float(batch.unit_price) if batch and hasattr(batch, 'unit_price') else 10.00,
            "batch_id": str(batch.id) if batch else "00000000-0000-0000-0000-000000000000",
            "batch_number": batch.batch_number if batch else "N/A",
        })
    return results

@router.get("/inventory/low-stock", response_model=list[InventoryItemOut])
async def list_low_stock(db: DBSession, _: CurrentUser):
    svc = InventoryService(db)
    return await svc.get_low_stock()

@router.get("/inventory", response_model=list[InventoryItemOut])
async def list_inventory(db: DBSession, _: CurrentUser, limit: int = 100):
    svc = InventoryService(db)
    return await svc.get_inventory(limit=limit)

@router.post("/inventory", response_model=InventoryItemOut)
async def create_inventory_item(data: InventoryItemCreate, db: DBSession, _: CurrentUser):
    svc = InventoryService(db)
    return await svc.create_inventory_item(data)

@router.post("/inventory/{drug_id}/update", response_model=InventoryItemOut)
async def update_inventory(drug_id: uuid.UUID, data: InventoryItemUpdate, db: DBSession, user: CurrentUser):
    svc = InventoryService(db)
    return await svc.update_inventory(drug_id, data, user.id)
