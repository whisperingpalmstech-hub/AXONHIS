from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.core.cssd.schemas import (
    InstrumentSetCreate, InstrumentSetOut,
    SterilizationCycleCreate, SterilizationCycleStatusUpdate, SterilizationCycleOut,
    CSSDDispatchCreate, CSSDDispatchReturn, CSSDDispatchOut
)
from app.core.cssd.services import CSSDService

router = APIRouter()


# ─── Instrument Sets ────────────────────────────────────────
@router.post("/instrument-sets", response_model=InstrumentSetOut, status_code=status.HTTP_201_CREATED)
async def create_instrument_set(
    data: InstrumentSetCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CSSDService(db)
    return await service.create_instrument_set(data, current_user.org_id)


@router.get("/instrument-sets", response_model=List[InstrumentSetOut])
async def list_instrument_sets(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CSSDService(db)
    return await service.get_instrument_sets(current_user.org_id)


# ─── Sterilization Cycles ───────────────────────────────────
@router.post("/cycles", response_model=SterilizationCycleOut, status_code=status.HTTP_201_CREATED)
async def create_cycle(
    data: SterilizationCycleCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CSSDService(db)
    return await service.create_cycle(data, current_user.id, current_user.org_id)


@router.get("/cycles", response_model=List[SterilizationCycleOut])
async def list_cycles(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CSSDService(db)
    return await service.get_cycles(current_user.org_id)


@router.put("/cycles/{cycle_id}/status", response_model=SterilizationCycleOut)
async def update_cycle_status(
    cycle_id: uuid.UUID,
    data: SterilizationCycleStatusUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CSSDService(db)
    return await service.update_cycle_status(cycle_id, data, current_user.org_id)


# ─── Dispatches ─────────────────────────────────────────────
@router.post("/dispatches", response_model=CSSDDispatchOut, status_code=status.HTTP_201_CREATED)
async def dispatch_set(
    data: CSSDDispatchCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CSSDService(db)
    return await service.dispatch_set(data, current_user.id, current_user.org_id)


@router.get("/dispatches", response_model=List[CSSDDispatchOut])
async def list_dispatches(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CSSDService(db)
    return await service.get_dispatches(current_user.org_id)


@router.put("/dispatches/{dispatch_id}/return", response_model=CSSDDispatchOut)
async def return_dispatch(
    dispatch_id: uuid.UUID,
    data: CSSDDispatchReturn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CSSDService(db)
    return await service.return_dispatch(dispatch_id, data, current_user.org_id)


# ─── Dashboard Stats ────────────────────────────────────────
@router.get("/stats")
async def get_cssd_stats(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = CSSDService(db)
    return await service.get_stats(current_user.org_id)
