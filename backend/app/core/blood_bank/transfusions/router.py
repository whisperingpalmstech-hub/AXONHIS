from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from .schemas import TransfusionCreate, TransfusionUpdate, TransfusionResponse
from .services import TransfusionService

router = APIRouter()

@router.post("", response_model=TransfusionResponse, status_code=status.HTTP_201_CREATED)
async def create_transfusion(
    transfusion_in: TransfusionCreate,
    session: AsyncSession = Depends(get_db),
):
    return await TransfusionService.create_transfusion(session, transfusion_in)

@router.get("", response_model=list[TransfusionResponse])
async def list_transfusions(
    session: AsyncSession = Depends(get_db),
):
    return await TransfusionService.list_transfusions(session)

@router.get("/{transfusion_id}", response_model=TransfusionResponse)
async def get_transfusion(
    transfusion_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    return await TransfusionService.get_transfusion(session, transfusion_id)

@router.patch("/{transfusion_id}", response_model=TransfusionResponse)
async def update_transfusion(
    transfusion_id: UUID,
    transfusion_in: TransfusionUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await TransfusionService.update_transfusion(session, transfusion_id, transfusion_in)
