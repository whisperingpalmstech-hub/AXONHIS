import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from .schemas import InventoryItemCreate, InventoryItemUpdate, InventoryItemOut
from .services import InventoryService

router = APIRouter(tags=["pharmacy-inventory"])

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
