import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from .schemas import DrugBatchCreate, DrugBatchOut
from .services import BatchService

router = APIRouter(tags=["pharmacy-batches"])

@router.get("/batches/near-expiry", response_model=list[DrugBatchOut])
async def list_near_expiry_batches(db: DBSession, _: CurrentUser, days: int = 30):
    svc = BatchService(db)
    return await svc.get_near_expiry_batches(days=days)

@router.get("/batches", response_model=list[DrugBatchOut])
async def list_batches(db: DBSession, _: CurrentUser, limit: int = 100):
    svc = BatchService(db)
    return await svc.list_batches(limit=limit)

@router.post("/batches", response_model=DrugBatchOut)
async def create_batch(data: DrugBatchCreate, db: DBSession, _: CurrentUser):
    svc = BatchService(db)
    return await svc.create_batch(data)
