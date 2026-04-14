from fastapi import APIRouter, Depends
from typing import List, Optional
import uuid

from app.dependencies import DBSession, CurrentUser
from .schemas import StoreOut, StoreBase, ItemOut, ItemBase, OpeningBalance, IndentCreate, IssueCreate, PhysicalAdjustment
from .services import InventoryService

router = APIRouter()

@router.post("/stores", response_model=StoreOut)
async def create_store(data: StoreBase, db: DBSession, user: CurrentUser):
    return await InventoryService(db).create_store(data)

@router.get("/stores", response_model=List[StoreOut])
async def get_stores(db: DBSession, user: CurrentUser):
    return await InventoryService(db).get_stores()

@router.get("/items", response_model=List[ItemOut])
async def get_items(db: DBSession, user: CurrentUser):
    return await InventoryService(db).get_items()

@router.get("/stock-levels")
async def get_stock_levels(db: DBSession, user: CurrentUser, store_id: Optional[uuid.UUID] = None):
    return await InventoryService(db).get_stock_levels(store_id)

@router.get("/stock-movements")
async def get_stock_movements(db: DBSession, user: CurrentUser, limit: int = 50):
    return await InventoryService(db).get_stock_movements(limit)

@router.get("/expiry-alerts")
async def get_expiry_alerts(db: DBSession, user: CurrentUser, days: int = 90):
    return await InventoryService(db).get_expiry_alerts(days)

@router.post("/items", response_model=ItemOut)
async def create_item(data: ItemBase, db: DBSession, user: CurrentUser):
    return await InventoryService(db).create_item(data)

@router.post("/opening-balance")
async def add_opening_balance(data: OpeningBalance, db: DBSession, user: CurrentUser):
    return await InventoryService(db).add_opening_balance(data, user.id)

@router.post("/indents")
async def create_indent(data: IndentCreate, db: DBSession, user: CurrentUser):
    return await InventoryService(db).create_indent(data, user.id)

@router.post("/issues")
async def create_issue(data: IssueCreate, db: DBSession, user: CurrentUser):
    return await InventoryService(db).create_issue(data, user.id)

@router.get("/indents")
async def get_indents(db: DBSession, user: CurrentUser):
    return await InventoryService(db).get_indents()

@router.get("/issues")
async def get_issues(db: DBSession, user: CurrentUser):
    return await InventoryService(db).get_issues()

@router.post("/issues/{issue_id}/accept")
async def accept_issue(issue_id: uuid.UUID, db: DBSession, user: CurrentUser):
    return await InventoryService(db).accept_issue(issue_id, user.id)

@router.post("/indents/{indent_id}/approve")
async def approve_indent(indent_id: uuid.UUID, db: DBSession, user: CurrentUser):
    return await InventoryService(db).approve_indent(indent_id)

@router.get("/gate-passes")
async def get_gate_passes(db: DBSession, user: CurrentUser):
    return await InventoryService(db).get_gate_passes()

@router.get("/ledger-history/{item_id}")
async def get_ledger_history(item_id: uuid.UUID, db: DBSession, user: CurrentUser, store_id: Optional[uuid.UUID] = None):
    return await InventoryService(db).get_ledger_history(item_id, store_id)

@router.post("/adjustments")
async def process_adjustment(data: PhysicalAdjustment, db: DBSession, user: CurrentUser):
    return await InventoryService(db).process_adjustment(data, user.id)

@router.get("/analytics")
async def get_analytics(db: DBSession, user: CurrentUser):
    return await InventoryService(db).get_inventory_analytics()
