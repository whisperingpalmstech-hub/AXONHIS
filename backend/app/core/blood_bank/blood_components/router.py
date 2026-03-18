from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from .schemas import BloodComponentCreate, BloodComponentUpdate, BloodComponentResponse
from .services import BloodComponentService

router = APIRouter()

@router.post("", response_model=BloodComponentResponse, status_code=status.HTTP_201_CREATED)
async def create_component(
    component_in: BloodComponentCreate,
    session: AsyncSession = Depends(get_db),
):
    return await BloodComponentService.create_component(session, component_in)

@router.get("", response_model=list[BloodComponentResponse])
async def list_components(
    session: AsyncSession = Depends(get_db),
):
    return await BloodComponentService.list_components(session)

@router.get("/{component_id}", response_model=BloodComponentResponse)
async def get_component(
    component_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    return await BloodComponentService.get_component(session, component_id)

@router.patch("/{component_id}", response_model=BloodComponentResponse)
async def update_component(
    component_id: UUID,
    component_in: BloodComponentUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await BloodComponentService.update_component(session, component_id, component_in)

@router.delete("/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_component(
    component_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    await BloodComponentService.delete_component(session, component_id)
