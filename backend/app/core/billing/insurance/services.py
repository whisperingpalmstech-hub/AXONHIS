import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from .models import (
    InsuranceProvider, InsurancePackage, InsurancePolicy, 
    PreAuthorization, InsuranceClaim, ClaimItem
)
from ..billing_entries.models import BillingEntry

class InsuranceService:
    @staticmethod
    async def create_provider(db: AsyncSession, data: dict) -> InsuranceProvider:
        provider = InsuranceProvider(**data)
        db.add(provider)
        await db.commit()
        await db.refresh(provider)
        return provider

    @staticmethod
    async def list_providers(db: AsyncSession) -> List[InsuranceProvider]:
        res = await db.execute(select(InsuranceProvider))
        return res.scalars().all()

    @staticmethod
    async def create_package(db: AsyncSession, data: dict) -> InsurancePackage:
        package = InsurancePackage(**data)
        db.add(package)
        await db.commit()
        await db.refresh(package)
        return package

    @staticmethod
    async def list_packages(db: AsyncSession, provider_id: Optional[uuid.UUID] = None) -> List[InsurancePackage]:
        stmt = select(InsurancePackage)
        if provider_id:
            stmt = stmt.where(InsurancePackage.provider_id == provider_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_policy(db: AsyncSession, data: dict) -> InsurancePolicy:
        policy = InsurancePolicy(**data)
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        return policy

    @staticmethod
    async def get_patient_policies(db: AsyncSession, patient_id: uuid.UUID) -> List[InsurancePolicy]:
        stmt = (
            select(InsurancePolicy)
            .where(InsurancePolicy.patient_id == patient_id)
            .options(selectinload(InsurancePolicy.package).selectinload(InsurancePackage.provider))
            .order_by(InsurancePolicy.priority.asc())
        )
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_pre_auth(db: AsyncSession, data: dict) -> PreAuthorization:
        pre_auth = PreAuthorization(**data)
        db.add(pre_auth)
        await db.commit()
        await db.refresh(pre_auth)
        return pre_auth

    @staticmethod
    async def update_pre_auth(db: AsyncSession, auth_id: uuid.UUID, data: dict) -> PreAuthorization:
        stmt = update(PreAuthorization).where(PreAuthorization.id == auth_id).values(**data)
        await db.execute(stmt)
        await db.commit()
        res = await db.execute(select(PreAuthorization).where(PreAuthorization.id == auth_id))
        return res.scalar_one()

    @staticmethod
    async def create_claim(db: AsyncSession, data: dict, items: List[dict]) -> InsuranceClaim:
        claim = InsuranceClaim(**data)
        if "claim_number" not in data or not data["claim_number"]:
            claim.claim_number = f"CLM-{uuid.uuid4().hex[:8].upper()}"
        db.add(claim)
        await db.flush()
        
        for item_data in items:
            item = ClaimItem(claim_id=claim.id, **item_data)
            db.add(item)
            
        await db.commit()
        await db.refresh(claim)
        
        # Refresh items
        stmt = select(InsuranceClaim).where(InsuranceClaim.id == claim.id).options(selectinload(InsuranceClaim.items))
        res = await db.execute(stmt)
        return res.scalar_one()

    @staticmethod
    async def calculate_split(
        db: AsyncSession, 
        patient_id: uuid.UUID, 
        billing_entries: List[BillingEntry]
    ) -> List[Dict[str, Any]]:
        """
        World-class split billing logic.
        Calculates patient vs insurer responsibility.
        """
        policies = await InsuranceService.get_patient_policies(db, patient_id)
        
        results = []
        for entry in billing_entries:
            remaining_amount = Decimal(str(entry.total_price))
            payer_splits = []
            
            for policy in policies:
                if remaining_amount <= 0: break
                
                pkg = policy.package
                co_pay_percent = Decimal(str(pkg.default_co_pay_percent))
                coverage_percent = Decimal('100') - co_pay_percent
                
                # Check for category specific coverage in JSON
                if pkg.coverage_details and isinstance(pkg.coverage_details, dict):
                    # Attempt to find category override (this requires BillingService category)
                    # For simplicity, if we don't have cat here, we use default
                    pass

                covered_amount = (remaining_amount * (coverage_percent / Decimal('100'))).quantize(Decimal('0.01'))
                
                if covered_amount > 0:
                    # Check for annual limit if needed
                    payer_splits.append({
                        "payer_id": policy.id,
                        "payer_name": f"{pkg.provider.provider_name} - {pkg.package_name}",
                        "type": "insurance",
                        "amount": float(covered_amount)
                    })
                    remaining_amount -= covered_amount
            
            if remaining_amount > 0:
                payer_splits.append({
                    "payer_id": patient_id,
                    "payer_name": "Patient",
                    "type": "patient",
                    "amount": float(remaining_amount)
                })
            
            results.append({
                "billing_entry_id": entry.id,
                "service_id": entry.service_id,
                "total_price": float(entry.total_price),
                "splits": payer_splits
            })
            
        return results
