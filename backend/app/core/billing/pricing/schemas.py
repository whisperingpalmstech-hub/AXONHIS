"""Variable Pricing Engine Schemas for Billing Module."""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class BaseRateCreate(BaseModel):
    """Schema for creating a base rate."""
    service_id: str
    service_name: str
    base_price: float
    is_active: bool = True


class BaseRateUpdate(BaseModel):
    """Schema for updating a base rate."""
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    base_price: Optional[float] = None
    is_active: Optional[bool] = None


class RateVariationCreate(BaseModel):
    """Schema for creating a rate variation."""
    base_rate_id: str
    patient_category: str
    bed_type: Optional[str] = None
    payment_entitlement: Optional[str] = None
    variation_type: str  # 'percentage', 'fixed', 'multiplier'
    variation_value: float
    validity_start_date: Optional[datetime] = None
    validity_end_date: Optional[datetime] = None
    is_active: bool = True


class RateValidityCreate(BaseModel):
    """Schema for creating a rate validity period."""
    base_rate_id: str
    valid_from: datetime
    valid_to: Optional[datetime] = None
    reason: Optional[str] = None


class AfterHoursChargeCreate(BaseModel):
    """Schema for creating after-hours charge."""
    service_id: str
    service_name: str
    start_time: str  # '18:00'
    end_time: str  # '08:00'
    days_applicable: List[str]
    charge_type: str  # 'percentage', 'fixed', 'multiplier'
    charge_value: float
    is_active: bool = True


class CurrencyCreate(BaseModel):
    """Schema for creating a currency."""
    currency_code: str = Field(..., max_length=3)
    currency_name: str
    currency_symbol: str
    is_base_currency: bool = False
    exchange_rate_to_base: float
    is_active: bool = True


class CurrencyUpdate(BaseModel):
    """Schema for updating a currency."""
    currency_name: Optional[str] = None
    currency_symbol: Optional[str] = None
    exchange_rate_to_base: Optional[float] = None
    is_active: Optional[bool] = None


class ExchangeRateCreate(BaseModel):
    """Schema for creating an exchange rate."""
    from_currency_id: str
    to_currency_id: str
    rate: float
    effective_from: datetime
    effective_to: Optional[datetime] = None
    source: Optional[str] = 'manual'


class PriceCalculationRequest(BaseModel):
    """Schema for price calculation request."""
    service_id: str
    patient_category: str
    bed_type: Optional[str] = None
    payment_entitlement: Optional[str] = None
    service_time: Optional[datetime] = None
    currency: Optional[str] = None


class PriceCalculationResponse(BaseModel):
    """Schema for price calculation response."""
    service_id: str
    base_price: float
    applicable_variation: Optional[float] = None
    after_hours_charge: Optional[float] = None
    final_price: float
    currency: str
    currency_symbol: str
    calculation_breakdown: dict
