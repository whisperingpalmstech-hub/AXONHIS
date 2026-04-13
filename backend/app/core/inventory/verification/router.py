"""Physical Stock Verification Router for Inventory."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.inventory.verification.schemas import (
    VerificationScheduleCreate, VerificationItemCreate, VerificationItemUpdate, DiscrepancyCreate
)
from app.core.inventory.verification.services import VerificationService

router = APIRouter()


@router.post("/verification-schedules")
async def create_verification_schedule(
    schedule_data: VerificationScheduleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a verification schedule."""
    service = VerificationService(db)
    return await service.create_verification_schedule(schedule_data, "system")


@router.get("/verification-schedules")
async def list_verification_schedules(
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """List verification schedules."""
    from app.core.inventory.verification.models import VerificationSchedule
    from sqlalchemy import select
    
    query = select(VerificationSchedule)
    if status:
        query = query.where(VerificationSchedule.status == status)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/verification-schedules/{schedule_id}/items")
async def add_verification_item(
    schedule_id: str,
    item_data: VerificationItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add an item to a verification schedule."""
    service = VerificationService(db)
    item_data.schedule_id = schedule_id
    return await service.add_verification_item(item_data)


@router.put("/verification-items/{item_id}/verify")
async def verify_item(
    item_id: str,
    update_data: VerificationItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Verify an item."""
    service = VerificationService(db)
    return await service.verify_item(item_id, update_data, "system")


@router.post("/discrepancies")
async def create_discrepancy(
    discrepancy_data: DiscrepancyCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a discrepancy record."""
    service = VerificationService(db)
    return await service.create_discrepancy(discrepancy_data)


@router.post("/verification-schedules/{schedule_id}/complete")
async def complete_verification(schedule_id: str, db: AsyncSession = Depends(get_db)):
    """Complete a verification schedule."""
    service = VerificationService(db)
    return await service.complete_verification(schedule_id)


@router.get("/verification-schedules/{schedule_id}/discrepancies")
async def get_discrepancies(schedule_id: str, db: AsyncSession = Depends(get_db)):
    """Get discrepancies for a verification schedule."""
    service = VerificationService(db)
    return await service.get_discrepancies(schedule_id)


@router.put("/discrepancies/{discrepancy_id}/resolve")
async def resolve_discrepancy(discrepancy_id: str, db: AsyncSession = Depends(get_db)):
    """Resolve a discrepancy."""
    service = VerificationService(db)
    return await service.resolve_discrepancy(discrepancy_id, "system")
