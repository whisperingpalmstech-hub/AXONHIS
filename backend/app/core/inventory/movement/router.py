"""Stock Movement Analytics Router for Inventory."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.core.inventory.movement.schemas import (
    StockTransferCreate, StockTransferItemCreate, StockTransferResponse,
    TransferApprovalCreate, MovementReportRequest
)
from app.core.inventory.movement.services import MovementService

router = APIRouter()


@router.post("/transfers", response_model=StockTransferResponse)
async def create_stock_transfer(
    transfer_data: StockTransferCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a stock transfer request."""
    service = MovementService(db)
    return await service.create_stock_transfer(transfer_data, "system")


@router.get("/transfers", response_model=List[StockTransferResponse])
async def list_transfers(
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """List stock transfers."""
    from app.core.inventory.movement.models import StockTransfer
    from sqlalchemy import select
    
    query = select(StockTransfer)
    if status:
        query = query.where(StockTransfer.status == status)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/transfers/{transfer_id}", response_model=StockTransferResponse)
async def get_transfer(transfer_id: str, db: AsyncSession = Depends(get_db)):
    """Get transfer details."""
    from app.core.inventory.movement.models import StockTransfer
    
    transfer = await db.get(StockTransfer, transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer


@router.post("/transfers/{transfer_id}/items")
async def add_transfer_item(
    transfer_id: str,
    item_data: StockTransferItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add an item to a transfer."""
    service = MovementService(db)
    return await service.add_transfer_item(transfer_id, item_data)


@router.post("/transfers/{transfer_id}/approve")
async def approve_transfer(
    transfer_id: str,
    approval_data: TransferApprovalCreate,
    db: AsyncSession = Depends(get_db)
):
    """Approve a transfer."""
    service = MovementService(db)
    return await service.approve_transfer(transfer_id, approval_data, "system")


@router.post("/transfers/{transfer_id}/execute")
async def execute_transfer(transfer_id: str, db: AsyncSession = Depends(get_db)):
    """Execute a transfer (ship items)."""
    service = MovementService(db)
    return await service.execute_transfer(transfer_id)


@router.post("/transfers/{transfer_id}/receive")
async def receive_transfer(transfer_id: str, db: AsyncSession = Depends(get_db)):
    """Receive a transfer."""
    service = MovementService(db)
    return await service.receive_transfer(transfer_id, "system")


@router.get("/transfers/{transfer_id}/status")
async def track_transfer_status(transfer_id: str, db: AsyncSession = Depends(get_db)):
    """Track transfer status."""
    service = MovementService(db)
    return await service.track_transfer_status(transfer_id)


@router.post("/reports/movement")
async def generate_movement_report(
    report_data: MovementReportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a movement report."""
    service = MovementService(db)
    return await service.generate_movement_report(report_data)


@router.get("/stores/{store_id}/movement-analytics")
async def get_store_movement_analytics(store_id: str, db: AsyncSession = Depends(get_db)):
    """Get movement analytics for a store."""
    service = MovementService(db)
    return await service.get_store_movement_analytics(store_id)


@router.get("/items/{item_id}/movement-history")
async def get_item_movement_history(item_id: str, db: AsyncSession = Depends(get_db)):
    """Get movement history for an item."""
    service = MovementService(db)
    return await service.get_item_movement_history(item_id)
