from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.core.linen.schemas import (
    LinenCategoryCreate, LinenCategoryOut,
    LinenInventoryLedgerOut,
    LaundryBatchCreate, LaundryBatchStatusUpdate, LaundryBatchOut,
    LinenTransactionCreate, LinenTransactionOut
)
from app.core.linen.services import LinenService

router = APIRouter()

@router.post("/categories", response_model=LinenCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: LinenCategoryCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LinenService(db)
    return await service.create_category(data, current_user.org_id)

@router.get("/categories", response_model=List[LinenCategoryOut])
async def list_categories(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LinenService(db)
    return await service.get_categories(current_user.org_id)

@router.post("/transactions", response_model=LinenTransactionOut, status_code=status.HTTP_201_CREATED)
async def log_transaction(
    data: LinenTransactionCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LinenService(db)
    return await service.log_transaction(data, current_user.id, current_user.org_id)

@router.get("/ledger", response_model=List[LinenInventoryLedgerOut])
async def get_inventory_ledger(
    department: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LinenService(db)
    return await service.get_ledger(department, current_user.org_id)

@router.post("/batches", response_model=LaundryBatchOut, status_code=status.HTTP_201_CREATED)
async def create_laundry_batch(
    data: LaundryBatchCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LinenService(db)
    return await service.create_batch(data, current_user.id, current_user.org_id)

@router.get("/batches", response_model=List[LaundryBatchOut])
async def list_laundry_batches(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LinenService(db)
    return await service.get_batches(current_user.org_id)

@router.put("/batches/{batch_id}/status", response_model=LaundryBatchOut)
async def update_batch_status(
    batch_id: uuid.UUID,
    data: LaundryBatchStatusUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = LinenService(db)
    return await service.update_batch_status(batch_id, data, current_user.org_id)
