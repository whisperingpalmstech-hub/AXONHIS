"""Taxation Module Services for Billing."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime, timezone

from app.core.billing.tax.models import Tax, TaxApplicability, TaxValidity
from app.core.billing.tax.schemas import (
    TaxCreate, TaxUpdate, TaxApplicabilityCreate, TaxValidityCreate
)


class TaxService:
    """Service for taxation operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_tax(self, tax_data: TaxCreate) -> Tax:
        """Create a new tax."""
        tax = Tax(**tax_data.model_dump())
        self.db.add(tax)
        await self.db.commit()
        await self.db.refresh(tax)
        return tax
    
    async def set_tax_applicability(self, applicability_data: TaxApplicabilityCreate) -> TaxApplicability:
        """Set tax applicability for a service."""
        applicability = TaxApplicability(**applicability_data.model_dump())
        self.db.add(applicability)
        await self.db.commit()
        await self.db.refresh(applicability)
        return applicability
    
    async def calculate_tax(self, service_id: str, amount: float, date: datetime) -> float:
        """Calculate tax for a service."""
        # Get applicable taxes for the service
        result = await self.db.execute(
            select(TaxApplicability).where(
                TaxApplicability.service_id == service_id,
                TaxApplicability.is_applicable == True
            )
        )
        applicabilities = result.scalars().all()
        
        total_tax = 0.0
        for applicability in applicabilities:
            # Get tax details
            tax = await self.db.get(Tax, applicability.tax_id)
            if not tax or not tax.is_active:
                continue
            
            # Check validity
            if tax.effective_from and date < tax.effective_from:
                continue
            if tax.effective_to and date > tax.effective_to:
                continue
            
            if applicability.validity_start_date and date < applicability.validity_start_date:
                continue
            if applicability.validity_end_date and date > applicability.validity_end_date:
                continue
            
            # Calculate tax
            tax_amount = amount * (tax.tax_percentage / 100)
            total_tax += tax_amount
        
        return total_tax
    
    async def get_applicable_tax(self, service_id: str, date: datetime) -> List[dict]:
        """Get applicable taxes for a service."""
        result = await self.db.execute(
            select(TaxApplicability).where(
                TaxApplicability.service_id == service_id,
                TaxApplicability.is_applicable == True
            )
        )
        applicabilities = result.scalars().all()
        
        applicable_taxes = []
        for applicability in applicabilities:
            tax = await self.db.get(Tax, applicability.tax_id)
            if not tax or not tax.is_active:
                continue
            
            # Check validity
            if tax.effective_from and date < tax.effective_from:
                continue
            if tax.effective_to and date > tax.effective_to:
                continue
            
            if applicability.validity_start_date and date < applicability.validity_start_date:
                continue
            if applicability.validity_end_date and date > applicability.validity_end_date:
                continue
            
            applicable_taxes.append({
                "tax_id": str(tax.id),
                "tax_code": tax.tax_code,
                "tax_name": tax.tax_name,
                "tax_type": tax.tax_type,
                "tax_percentage": float(tax.tax_percentage)
            })
        
        return applicable_taxes
    
    async def set_tax_validity(self, validity_data: TaxValidityCreate) -> TaxValidity:
        """Set tax validity period."""
        validity = TaxValidity(**validity_data.model_dump())
        self.db.add(validity)
        await self.db.commit()
        await self.db.refresh(validity)
        return validity
