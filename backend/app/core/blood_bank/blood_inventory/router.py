from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from .schemas import BloodStorageUnitCreate, BloodStorageUnitUpdate, BloodStorageUnitResponse
from .services import BloodInventoryService

router = APIRouter()

@router.post("", response_model=BloodStorageUnitResponse, status_code=status.HTTP_201_CREATED)
async def create_storage_unit(
    storage_in: BloodStorageUnitCreate,
    session: AsyncSession = Depends(get_db),
):
    return await BloodInventoryService.create_storage_unit(session, storage_in)

@router.get("", response_model=list[BloodStorageUnitResponse])
async def list_storage_units(
    session: AsyncSession = Depends(get_db),
):
    return await BloodInventoryService.list_storage_units(session)

@router.get("/{storage_id}", response_model=BloodStorageUnitResponse)
async def get_storage_unit(
    storage_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    return await BloodInventoryService.get_storage_unit(session, storage_id)

@router.patch("/{storage_id}", response_model=BloodStorageUnitResponse)
async def update_storage_unit(
    storage_id: UUID,
    storage_in: BloodStorageUnitUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await BloodInventoryService.update_storage_unit(session, storage_id, storage_in)

@router.delete("/{storage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_storage_unit(
    storage_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    await BloodInventoryService.delete_storage_unit(session, storage_id)
