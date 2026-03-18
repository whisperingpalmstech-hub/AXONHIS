from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from .schemas import (
    BloodDonorCreate, BloodDonorUpdate, BloodDonorResponse,
    BloodCollectionCreate, BloodCollectionResponse
)
from .services import BloodDonorService

router = APIRouter()

@router.post("", response_model=BloodDonorResponse, status_code=status.HTTP_201_CREATED)
async def create_donor(
    donor_in: BloodDonorCreate,
    session: AsyncSession = Depends(get_db),
):
    return await BloodDonorService.create_donor(session, donor_in)

@router.get("", response_model=list[BloodDonorResponse])
async def list_donors(
    session: AsyncSession = Depends(get_db),
):
    return await BloodDonorService.list_donors(session)

@router.get("/{donor_id}", response_model=BloodDonorResponse)
async def get_donor(
    donor_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    return await BloodDonorService.get_donor(session, donor_id)

@router.patch("/{donor_id}", response_model=BloodDonorResponse)
async def update_donor(
    donor_id: UUID,
    donor_in: BloodDonorUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await BloodDonorService.update_donor(session, donor_id, donor_in)

@router.post("/{donor_id}/collections", response_model=BloodCollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    donor_id: UUID,
    collection_in: BloodCollectionCreate,
    session: AsyncSession = Depends(get_db),
):
    if collection_in.donor_id != donor_id:
        collection_in.donor_id = donor_id
    return await BloodDonorService.create_collection(session, collection_in)

@router.get("/{donor_id}/collections", response_model=list[BloodCollectionResponse])
async def list_donor_collections(
    donor_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    return await BloodDonorService.get_donor_collections(session, donor_id)
