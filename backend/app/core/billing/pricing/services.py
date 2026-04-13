"""Variable Pricing Engine Services for Billing Module."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Dict, Any
from datetime import datetime, timezone, time

from app.core.billing.pricing.models import (
    BaseRate, RateVariation, RateValidity, AfterHoursCharge,
    Currency, ExchangeRate
)
from app.core.billing.pricing.schemas import (
    BaseRateCreate, BaseRateUpdate, RateVariationCreate, RateValidityCreate,
    AfterHoursChargeCreate, CurrencyCreate, CurrencyUpdate, ExchangeRateCreate,
    PriceCalculationRequest
)


class PricingService:
    """Service for variable pricing operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def set_base_rate(self, rate_data: BaseRateCreate) -> BaseRate:
        """Set base rate for a service."""
        base_rate = BaseRate(**rate_data.model_dump())
        self.db.add(base_rate)
        await self.db.commit()
        await self.db.refresh(base_rate)
        return base_rate
    
    async def update_base_rate(self, rate_id: str, rate_data: BaseRateUpdate) -> Optional[BaseRate]:
        """Update base rate."""
        base_rate = await self.db.get(BaseRate, rate_id)
        if not base_rate:
            return None
        
        update_data = rate_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(base_rate, field, value)
        
        base_rate.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(base_rate)
        return base_rate
    
    async def add_rate_variation(self, variation_data: RateVariationCreate) -> RateVariation:
        """Add a rate variation."""
        variation = RateVariation(**variation_data.model_dump())
        self.db.add(variation)
        await self.db.commit()
        await self.db.refresh(variation)
        return variation
    
    async def set_rate_validity(self, validity_data: RateValidityCreate) -> RateValidity:
        """Set rate validity period."""
        validity = RateValidity(**validity_data.model_dump())
        self.db.add(validity)
        await self.db.commit()
        await self.db.refresh(validity)
        return validity
    
    async def apply_after_hours_charge(
        self, base_price: float, service_id: str, service_time: datetime
    ) -> float:
        """Apply after-hours charging if applicable."""
        # Get after-hours charge rules for the service
        result = await self.db.execute(
            select(AfterHoursCharge).where(
                AfterHoursCharge.service_id == service_id,
                AfterHoursCharge.is_active == True
            )
        )
        charges = result.scalars().all()
        
        if not charges:
            return base_price
        
        # Check if service time is within after-hours
        service_time_obj = service_time.time()
        service_day = service_time.strftime("%A").lower()
        
        for charge in charges:
            # Check if day is applicable
            if service_day not in charge.days_applicable:
                continue
            
            # Parse start and end times
            start_time = datetime.strptime(charge.start_time, "%H:%M").time()
            end_time = datetime.strptime(charge.end_time, "%H:%M").time()
            
            # Check if time is within after-hours range
            if start_time <= end_time:
                # Same day range (e.g., 18:00 to 23:59)
                if start_time <= service_time_obj <= end_time:
                    return self._apply_charge(base_price, charge)
            else:
                # Overnight range (e.g., 18:00 to 08:00 next day)
                if service_time_obj >= start_time or service_time_obj <= end_time:
                    return self._apply_charge(base_price, charge)
        
        return base_price
    
    def _apply_charge(self, base_price: float, charge: AfterHoursCharge) -> float:
        """Apply charge based on charge type."""
        if charge.charge_type == "percentage":
            return base_price * (1 + charge.charge_value / 100)
        elif charge.charge_type == "fixed":
            return base_price + charge.charge_value
        elif charge.charge_type == "multiplier":
            return base_price * charge.charge_value
        return base_price
    
    async def apply_rate_validity(self, base_rate_id: str, date: datetime) -> bool:
        """Check if rate is valid on a given date."""
        result = await self.db.execute(
            select(RateValidity).where(
                RateValidity.base_rate_id == base_rate_id
            )
        )
        validities = result.scalars().all()
        
        if not validities:
            return True  # No validity restrictions
        
        for validity in validities:
            if validity.valid_from <= date <= (validity.valid_to or datetime.max):
                return True
        
        return False
    
    async def calculate_service_price(
        self, request: PriceCalculationRequest
    ) -> Dict[str, Any]:
        """Calculate service price based on patient context."""
        # Get base rate
        result = await self.db.execute(
            select(BaseRate).where(
                BaseRate.service_id == request.service_id,
                BaseRate.is_active == True
            )
        )
        base_rate = result.scalar_one_or_none()
        
        if not base_rate:
            return {
                "service_id": request.service_id,
                "base_price": 0,
                "applicable_variation": None,
                "after_hours_charge": None,
                "final_price": 0,
                "currency": "INR",
                "currency_symbol": "₹",
                "calculation_breakdown": {"error": "Base rate not found"}
            }
        
        base_price = float(base_rate.base_price)
        final_price = base_price
        breakdown = {"base_price": base_price}
        
        # Apply rate variation
        result = await self.db.execute(
            select(RateVariation).where(
                RateVariation.base_rate_id == base_rate.id,
                RateVariation.patient_category == request.patient_category,
                RateVariation.is_active == True
            )
        )
        variations = result.scalars().all()
        
        applicable_variation = None
        for variation in variations:
            # Check bed type match
            if variation.bed_type and variation.bed_type != request.bed_type:
                continue
            
            # Check payment entitlement match
            if variation.payment_entitlement and variation.payment_entitlement != request.payment_entitlement:
                continue
            
            # Check validity
            if variation.validity_start_date or variation.validity_end_date:
                now = datetime.now(timezone.utc)
                if variation.validity_start_date and now < variation.validity_start_date:
                    continue
                if variation.validity_end_date and now > variation.validity_end_date:
                    continue
            
            # Apply variation
            if variation.variation_type == "percentage":
                final_price = final_price * (1 + variation.variation_value / 100)
            elif variation.variation_type == "fixed":
                final_price = final_price + variation.variation_value
            elif variation.variation_type == "multiplier":
                final_price = final_price * variation.variation_value
            
            applicable_variation = variation.variation_value
            breakdown["variation"] = {
                "type": variation.variation_type,
                "value": variation.variation_value
            }
            break
        
        # Apply after-hours charge
        after_hours_charge = None
        if request.service_time:
            price_with_after_hours = await self.apply_after_hours_charge(
                final_price, request.service_id, request.service_time
            )
            if price_with_after_hours != final_price:
                after_hours_charge = price_with_after_hours - final_price
                final_price = price_with_after_hours
                breakdown["after_hours_charge"] = after_hours_charge
        
        # Currency conversion if needed
        currency = request.currency or "INR"
        currency_symbol = "₹"
        if currency != "INR":
            result = await self.db.execute(
                select(Currency).where(
                    Currency.currency_code == currency,
                    Currency.is_active == True
                )
            )
            currency_obj = result.scalar_one_or_none()
            if currency_obj:
                currency_symbol = currency_obj.currency_symbol
                if not currency_obj.is_base_currency:
                    final_price = final_price * currency_obj.exchange_rate_to_base
                    breakdown["currency_conversion"] = {
                        "from": "INR",
                        "to": currency,
                        "rate": currency_obj.exchange_rate_to_base
                    }
        
        breakdown["final_price"] = final_price
        
        return {
            "service_id": request.service_id,
            "base_price": base_price,
            "applicable_variation": applicable_variation,
            "after_hours_charge": after_hours_charge,
            "final_price": round(final_price, 2),
            "currency": currency,
            "currency_symbol": currency_symbol,
            "calculation_breakdown": breakdown
        }
    
    async def add_currency(self, currency_data: CurrencyCreate) -> Currency:
        """Add a new currency."""
        currency = Currency(**currency_data.model_dump())
        self.db.add(currency)
        await self.db.commit()
        await self.db.refresh(currency)
        return currency
    
    async def update_exchange_rates(self, from_currency_id: str, to_currency_id: str, rate: float) -> ExchangeRate:
        """Update exchange rate."""
        exchange_rate = ExchangeRate(
            from_currency_id=from_currency_id,
            to_currency_id=to_currency_id,
            rate=rate,
            effective_from=datetime.now(timezone.utc),
            source="manual"
        )
        self.db.add(exchange_rate)
        await self.db.commit()
        await self.db.refresh(exchange_rate)
        return exchange_rate
    
    async def get_applicable_rate(self, service_id: str, date: datetime, patient_context: Dict[str, Any]) -> float:
        """Get applicable rate for a service."""
        request = PriceCalculationRequest(
            service_id=service_id,
            patient_category=patient_context.get("patient_category", "national"),
            bed_type=patient_context.get("bed_type"),
            payment_entitlement=patient_context.get("payment_entitlement"),
            service_time=date
        )
        result = await self.calculate_service_price(request)
        return result["final_price"]
    
    async def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount between currencies."""
        if from_currency == to_currency:
            return amount
        
        # Get exchange rate
        result = await self.db.execute(
            select(Currency).where(Currency.currency_code == from_currency)
        )
        from_curr = result.scalar_one_or_none()
        
        result = await self.db.execute(
            select(Currency).where(Currency.currency_code == to_currency)
        )
        to_curr = result.scalar_one_or_none()
        
        if not from_curr or not to_curr:
            return amount
        
        # Convert via base currency
        amount_in_base = amount if from_curr.is_base_currency else amount / from_curr.exchange_rate_to_base
        final_amount = amount_in_base if to_curr.is_base_currency else amount_in_base * to_curr.exchange_rate_to_base
        
        return round(final_amount, 2)
