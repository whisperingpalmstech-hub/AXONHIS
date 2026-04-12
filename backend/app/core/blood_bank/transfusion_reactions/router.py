from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from .schemas import TransfusionReactionCreate, TransfusionReactionUpdate, TransfusionReactionResponse
from .services import TransfusionReactionService

router = APIRouter()

@router.post("", response_model=TransfusionReactionResponse, status_code=status.HTTP_201_CREATED)
async def create_reaction(
    reaction_in: TransfusionReactionCreate,
    session: AsyncSession = Depends(get_db),
):
    return await TransfusionReactionService.create_reaction(session, reaction_in)

@router.get("", response_model=list[TransfusionReactionResponse])
async def list_reactions(
    session: AsyncSession = Depends(get_db),
):
    return await TransfusionReactionService.list_reactions(session)

@router.get("/{reaction_id}", response_model=TransfusionReactionResponse)
async def get_reaction(
    reaction_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    return await TransfusionReactionService.get_reaction(session, reaction_id)

@router.patch("/{reaction_id}", response_model=TransfusionReactionResponse)
async def update_reaction(
    reaction_id: UUID,
    reaction_in: TransfusionReactionUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await TransfusionReactionService.update_reaction(session, reaction_id, reaction_in)
