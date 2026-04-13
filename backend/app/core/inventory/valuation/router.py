"""Stock Valuation Router for Inventory."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.inventory.valuation.schemas import (
    ValuationMethodCreate, StockValuationRequest, StockAdjustmentCreate
)
from app.core.inventory.valuation.services import ValuationService

router = APIRouter()


@router.post("/valuation-methods")
async def create_valuation_method(
    method_data: ValuationMethodCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a valuation method."""
    service = ValuationService(db)
    return await service.create_valuation_method(method_data)


@router.post("/valuations")
async def calculate_stock_value(
    request: StockValuationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Calculate stock value using specified method."""
    service = ValuationService(db)
    return await service.calculate_stock_value(request, "system")


@router.post("/stock-adjustments")
async def create_stock_adjustment(
    adjustment_data: StockAdjustmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a stock adjustment."""
    service = ValuationService(db)
    return await service.create_stock_adjustment(adjustment_data, "system")


@router.get("/stores/{store_id}/valuation")
async def get_store_valuation(
    store_id: str,
    valuation_date: str,
    db: AsyncSession = Depends(get_db)
):
    """Get valuation for a store on a specific date."""
    from datetime import datetime
    service = ValuationService(db)
    valuation = await service.get_store_valuation(store_id, datetime.fromisoformat(valuation_date))
    if not valuation:
        raise HTTPException(status_code=404, detail="Valuation not found")
    return valuation


@router.get("/items/{item_id}/valuation")
async def get_item_valuation(
    item_id: str,
    valuation_date: str,
    db: AsyncSession = Depends(get_db)
):
    """Get valuation for an item."""
    from datetime import datetime
    service = ValuationService(db)
    return await service.get_item_valuation(item_id, datetime.fromisoformat(valuation_date))


@router.get("/items/{item_id}/fifo-value")
async def calculate_fifo_value(
    item_id: str,
    store_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Calculate FIFO value for an item."""
    service = ValuationService(db)
    value = await service.calculate_fifo_value(item_id, store_id)
    return {"item_id": item_id, "fifo_value": value}


@router.get("/items/{item_id}/lifo-value")
async def calculate_lifo_value(
    item_id: str,
    store_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Calculate LIFO value for an item."""
    service = ValuationService(db)
    value = await service.calculate_lifo_value(item_id, store_id)
    return {"item_id": item_id, "lifo_value": value}
