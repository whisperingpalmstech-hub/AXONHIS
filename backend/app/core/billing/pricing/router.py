"""Variable Pricing Engine Router for Billing Module."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database import get_db
from app.core.billing.pricing.schemas import (
    BaseRateCreate, BaseRateUpdate, RateVariationCreate, RateValidityCreate,
    AfterHoursChargeCreate, CurrencyCreate, CurrencyUpdate, ExchangeRateCreate,
    PriceCalculationRequest, PriceCalculationResponse
)
from app.core.billing.pricing.services import PricingService

router = APIRouter()


@router.post("/rates")
async def set_base_rate(
    rate_data: BaseRateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Set base rate for a service."""
    service = PricingService(db)
    return await service.set_base_rate(rate_data)


@router.put("/rates/{rate_id}")
async def update_base_rate(
    rate_id: str,
    rate_data: BaseRateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update base rate."""
    service = PricingService(db)
    rate = await service.update_base_rate(rate_id, rate_data)
    if not rate:
        raise HTTPException(status_code=404, detail="Base rate not found")
    return rate


@router.post("/variations")
async def add_rate_variation(
    variation_data: RateVariationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a rate variation."""
    service = PricingService(db)
    return await service.add_rate_variation(variation_data)


@router.post("/validity")
async def set_rate_validity(
    validity_data: RateValidityCreate,
    db: AsyncSession = Depends(get_db)
):
    """Set rate validity period."""
    service = PricingService(db)
    return await service.set_rate_validity(validity_data)


@router.post("/calculate", response_model=PriceCalculationResponse)
async def calculate_price(
    request: PriceCalculationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Calculate service price based on patient context."""
    service = PricingService(db)
    result = await service.calculate_service_price(request)
    return PriceCalculationResponse(**result)


@router.post("/currencies")
async def add_currency(
    currency_data: CurrencyCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a new currency."""
    service = PricingService(db)
    return await service.add_currency(currency_data)


@router.put("/currencies/{currency_id}")
async def update_currency(
    currency_id: str,
    currency_data: CurrencyUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update currency exchange rate."""
    service = PricingService(db)
    return await service.update_exchange_rates(currency_id, currency_id, currency_data.exchange_rate_to_base)


@router.get("/rates/{service_id}/applicable")
async def get_applicable_rate(
    service_id: str,
    patient_category: str,
    bed_type: str = None,
    payment_entitlement: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get applicable rate for a service."""
    from datetime import datetime, timezone
    service = PricingService(db)
    patient_context = {
        "patient_category": patient_category,
        "bed_type": bed_type,
        "payment_entitlement": payment_entitlement
    }
    rate = await service.get_applicable_rate(service_id, datetime.now(timezone.utc), patient_context)
    return {"service_id": service_id, "applicable_rate": rate}
