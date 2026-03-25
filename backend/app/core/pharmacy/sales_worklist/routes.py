import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

from .schemas import PharmacySalesWorklistOut, DispenseRequest, PharmacyDispenseLogOut
from .services import SalesWorklistService

router = APIRouter(prefix="/sales-worklist", tags=["OP Pharmacy Sales Worklist"])

@router.get("", response_model=List[PharmacySalesWorklistOut])
async def list_worklists(status: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    """List pending OP Pharmacy Prescriptions"""
    svc = SalesWorklistService(db)
    wls = await svc.get_worklists(status)
    return wls

@router.get("/{worklist_id}", response_model=PharmacySalesWorklistOut)
async def get_worklist(worklist_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get full details of a specific prescription in worklist"""
    svc = SalesWorklistService(db)
    return await svc.get_worklist(worklist_id)

@router.post("/{worklist_id}/dispense")
async def process_dispense(worklist_id: uuid.UUID, data: DispenseRequest, db: AsyncSession = Depends(get_db)):
    """Process a prescription: validations, dispensing, stock update, and billing trigger"""
    svc = SalesWorklistService(db)
    try:
        await svc.process_dispense(worklist_id, data)
        return {"status": "success", "message": "Medications dispensed successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{worklist_id}/audit", response_model=List[PharmacyDispenseLogOut])
async def get_dispensing_logs(worklist_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get immutable audit logs for dispensing actions"""
    svc = SalesWorklistService(db)
    return await svc.get_dispensing_logs(worklist_id)

@router.post("/seed_mock_data")
async def seed_mock(db: AsyncSession = Depends(get_db)):
    """Seed the system with sample prescriptions for testing."""
    svc = SalesWorklistService(db)
    wl = await svc.mock_seed_worklist()
    return {"status": "success", "worklist_id": wl.id}
