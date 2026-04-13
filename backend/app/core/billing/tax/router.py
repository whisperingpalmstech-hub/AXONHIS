"""Taxation Module Router for Billing."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.core.billing.tax.schemas import (
    TaxCreate, TaxUpdate, TaxApplicabilityCreate, TaxValidityCreate
)
from app.core.billing.tax.services import TaxService

router = APIRouter()


@router.post("/taxes")
async def create_tax(
    tax_data: TaxCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tax."""
    service = TaxService(db)
    return await service.create_tax(tax_data)


@router.get("/taxes")
async def list_taxes(
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List all taxes."""
    from app.core.billing.tax.models import Tax
    from sqlalchemy import select
    
    query = select(Tax).where(Tax.is_active == is_active)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/taxes/applicability")
async def set_tax_applicability(
    applicability_data: TaxApplicabilityCreate,
    db: AsyncSession = Depends(get_db)
):
    """Set tax applicability for a service."""
    service = TaxService(db)
    return await service.set_tax_applicability(applicability_data)


@router.get("/taxes/applicable/{service_id}")
async def get_applicable_tax(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get applicable taxes for a service."""
    from datetime import datetime, timezone
    service = TaxService(db)
    return await service.get_applicable_tax(service_id, datetime.now(timezone.utc))


@router.post("/taxes/validity")
async def set_tax_validity(
    validity_data: TaxValidityCreate,
    db: AsyncSession = Depends(get_db)
):
    """Set tax validity period."""
    service = TaxService(db)
    return await service.set_tax_validity(validity_data)
