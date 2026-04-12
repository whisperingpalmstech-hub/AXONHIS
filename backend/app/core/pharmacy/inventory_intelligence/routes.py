import uuid
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

from .schemas import BatchCreate, BatchOut, KitCreate, KitOut, AlertOut, AnalysisUpdate, AnalysisOut
from .services import InventoryIntelligenceService

router = APIRouter()

@router.post("/batches", response_model=BatchOut, status_code=201)
async def register_inventory_batch(
    data: BatchCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Register a new batch of drugs into specific multi-store."""
    svc = InventoryIntelligenceService(db)
    user_id = uuid.uuid4() # mock user ID from context
    return await svc.register_batch(data, user_id)

@router.post("/kits", response_model=KitOut, status_code=201)
async def define_item_kit(
    data: KitCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create bundled medication preconfigured kit."""
    svc = InventoryIntelligenceService(db)
    user_id = uuid.uuid4() # mock user ID from context
    return await svc.create_kit(data, user_id)

@router.get("/kits", response_model=List[KitOut])
async def list_item_kits(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """List all available predefined medication kits."""
    svc = InventoryIntelligenceService(db)
    return await svc.get_kits()

@router.patch("/kits/{kit_id}", response_model=KitOut)
async def update_item_kit(
    kit_id: uuid.UUID,
    kit_components: List[dict],
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update component list in a kit."""
    svc = InventoryIntelligenceService(db)
    return await svc.update_kit(kit_id, kit_components)

@router.post("/analysis/expiries")
async def trigger_expiry_detector(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Manually trigger background processor to detect expiring medicines."""
    svc = InventoryIntelligenceService(db)
    await svc.analyze_expiries()
    return {"message": "Expiry analysis completed."}

@router.patch("/analysis/{drug_id}", response_model=AnalysisOut)
async def update_inventory_analysis(
    drug_id: uuid.UUID,
    data: AnalysisUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Classify 100ABC or VED status for item intelligence optimization."""
    svc = InventoryIntelligenceService(db)
    return await svc.update_analysis(
        drug_id, 
        abc_category=data.abc_category, 
        ved_category=data.ved_category, 
        is_dead_stock=data.is_dead_stock
    )

@router.get("/alerts", response_model=List[AlertOut])
async def list_inventory_alerts(
    store_id: str = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """See smart alerts (Reorder thresholds breached, Expiry risks, Dead Stock)."""
    svc = InventoryIntelligenceService(db)
    return await svc.get_alerts(store_id)
