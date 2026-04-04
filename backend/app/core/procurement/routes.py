from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
import uuid

from app.database import get_db
from app.dependencies import get_current_user
from app.core.auth.models import User

from .schemas import (
    VendorMasterCreate, VendorMasterOut,
    PurchaseRequestCreate, PurchaseRequestOut,
    PurchaseOrderCreate, PurchaseOrderOut,
    GRNCreate, GRNOut, GRNInspectionCommand
)
from .services import ProcurementService

router = APIRouter(prefix="/procurement", tags=["Procurement & Sourcing"])

@router.get("/utils/stores")
async def list_stores_for_procurement(db: AsyncSession = Depends(get_db)):
    return await ProcurementService.get_stores(db)

@router.get("/utils/items")
async def list_items_for_procurement(db: AsyncSession = Depends(get_db)):
    return await ProcurementService.get_items(db)

@router.get("/vendors", response_model=List[VendorMasterOut])
async def list_vendors(db: AsyncSession = Depends(get_db)):
    return await ProcurementService.get_vendors(db)

@router.post("/vendors", response_model=VendorMasterOut)
async def add_vendor(data: VendorMasterCreate, db: AsyncSession = Depends(get_db)):
    return await ProcurementService.create_vendor(db, data)

@router.get("/requests", response_model=List[PurchaseRequestOut])
async def list_prs(db: AsyncSession = Depends(get_db)):
    return await ProcurementService.get_prs(db)

@router.post("/requests", response_model=PurchaseRequestOut)
async def create_pr(data: PurchaseRequestCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await ProcurementService.create_pr(db, data, current_user.id)

@router.post("/requests/{pr_id}/approve", response_model=PurchaseRequestOut)
async def approve_pr(pr_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await ProcurementService.approve_pr(db, pr_id)

@router.get("/orders", response_model=List[PurchaseOrderOut])
async def list_pos(db: AsyncSession = Depends(get_db)):
    return await ProcurementService.get_pos(db)

@router.post("/orders", response_model=PurchaseOrderOut)
async def create_po(data: PurchaseOrderCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await ProcurementService.create_po(db, data, current_user.id)

@router.get("/grn", response_model=List[GRNOut])
async def list_grns(db: AsyncSession = Depends(get_db)):
    return await ProcurementService.get_grns(db)

@router.post("/grn", response_model=GRNOut)
async def create_grn(data: GRNCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await ProcurementService.create_grn(db, data, current_user.id)

@router.post("/grn/{grn_id}/inspect", response_model=GRNOut)
async def inspect_grn(grn_id: uuid.UUID, inspections: Dict[str, GRNInspectionCommand], db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await ProcurementService.inspect_and_sync_grn(db, grn_id, inspections)
