from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from .schemas import BloodUnitCreate, BloodUnitUpdate, BloodUnitResponse
from .services import BloodUnitService

router = APIRouter()

@router.post("", response_model=BloodUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_unit(
    unit_in: BloodUnitCreate,
    session: AsyncSession = Depends(get_db),
):
    return await BloodUnitService.create_unit(session, unit_in)

@router.get("", response_model=list[BloodUnitResponse])
async def list_units(
    unit_status: Optional[str] = Query(None, description="Filter by status (available, reserved, etc)"),
    session: AsyncSession = Depends(get_db),
):
    return await BloodUnitService.list_units(session, status=unit_status)

@router.get("/{unit_id}", response_model=BloodUnitResponse)
async def get_unit(
    unit_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    return await BloodUnitService.get_unit(session, unit_id)

@router.patch("/{unit_id}", response_model=BloodUnitResponse)
async def update_unit(
    unit_id: UUID,
    unit_in: BloodUnitUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await BloodUnitService.update_unit(session, unit_id, unit_in)
