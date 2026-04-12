from fastapi import APIRouter, Depends
from typing import List
import uuid

from app.dependencies import DBSession, CurrentUser
from .schemas import StoreOut, StoreBase, ItemOut, ItemBase, OpeningBalance, IndentCreate, IssueCreate
from .services import InventoryService

router = APIRouter()

@router.post("/stores", response_model=StoreOut)
async def create_store(data: StoreBase, db: DBSession, user: CurrentUser):
    return await InventoryService(db).create_store(data)

@router.get("/stores", response_model=List[StoreOut])
async def get_stores(db: DBSession, user: CurrentUser):
    return await InventoryService(db).get_stores()

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

@router.put("/issues/{issue_id}/accept")
async def accept_issue(issue_id: uuid.UUID, db: DBSession, user: CurrentUser):
    return await InventoryService(db).accept_issue(issue_id, user.id)
