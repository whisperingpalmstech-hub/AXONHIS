from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from .schemas import CrossmatchTestCreate, CrossmatchTestUpdate, CrossmatchTestResponse
from .services import CompatibilityTestService

router = APIRouter()

@router.post("", response_model=CrossmatchTestResponse, status_code=status.HTTP_201_CREATED)
async def create_crossmatch(
    test_in: CrossmatchTestCreate,
    session: AsyncSession = Depends(get_db),
):
    return await CompatibilityTestService.create_crossmatch(session, test_in)

@router.get("", response_model=list[CrossmatchTestResponse])
async def list_crossmatches(
    session: AsyncSession = Depends(get_db),
):
    return await CompatibilityTestService.list_crossmatches(session)

@router.get("/{test_id}", response_model=CrossmatchTestResponse)
async def get_crossmatch(
    test_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    return await CompatibilityTestService.get_crossmatch(session, test_id)

@router.patch("/{test_id}", response_model=CrossmatchTestResponse)
async def update_crossmatch(
    test_id: UUID,
    test_in: CrossmatchTestUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await CompatibilityTestService.update_crossmatch(session, test_id, test_in)
