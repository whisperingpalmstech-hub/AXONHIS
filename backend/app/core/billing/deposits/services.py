"""Deposit Management Services for Billing Module."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime, timezone
import random

from app.core.billing.deposits.models import (
    Deposit, DepositUsage, DepositRefund, FamilyDeposit,
    FamilyDepositMember, FamilyDepositOTP
)
from app.core.billing.deposits.schemas import (
    DepositCreate, DepositRefundCreate, FamilyDepositCreate,
    FamilyDepositMemberCreate, FamilyDepositOTPValidate
)


class DepositService:
    """Service for deposit management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_deposit(self, deposit_data: DepositCreate, received_by: str) -> Deposit:
        """Create a new deposit."""
        # Generate deposit number
        result = await self.db.execute(select(func.max(Deposit.id)))
        max_id = result.scalar()
        deposit_number = f"DEP-{datetime.now().strftime('%Y%m%d')}-{(max_id or 0) + 1:04d}"
        
        deposit = Deposit(
            **deposit_data.model_dump(),
            deposit_number=deposit_number,
            received_by=received_by
        )
        self.db.add(deposit)
        await self.db.commit()
        await self.db.refresh(deposit)
        return deposit
    
    async def use_deposit(self, deposit_id: str, bill_id: str, amount: float, used_by: str) -> DepositUsage:
        """Use deposit for a bill."""
        deposit = await self.db.get(Deposit, deposit_id)
        if not deposit or not deposit.is_active:
            raise ValueError("Deposit not found or inactive")
        
        # Check available amount
        result = await self.db.execute(
            select(func.sum(DepositUsage.amount_used)).where(
                DepositUsage.deposit_id == deposit_id
            )
        )
        used_amount = result.scalar() or 0
        available = deposit.amount - used_amount
        
        if amount > available:
            raise ValueError(f"Insufficient deposit balance. Available: {available}, Requested: {amount}")
        
        usage = DepositUsage(
            deposit_id=deposit_id,
            bill_id=bill_id,
            amount_used=amount,
            used_by=used_by
        )
        self.db.add(usage)
        await self.db.commit()
        await self.db.refresh(usage)
        return usage
    
    async def refund_deposit(self, deposit_id: str, refund_data: DepositRefundCreate, requested_by: str) -> DepositRefund:
        """Process a refund request."""
        deposit = await self.db.get(Deposit, deposit_id)
        if not deposit:
            raise ValueError("Deposit not found")
        
        if not deposit.is_refundable:
            raise ValueError("This deposit is not refundable")
        
        # Check if refund amount exceeds available
        result = await self.db.execute(
            select(func.sum(DepositUsage.amount_used)).where(
                DepositUsage.deposit_id == deposit_id
            )
        )
        used_amount = result.scalar() or 0
        available = deposit.amount - used_amount
        
        if refund_data.refund_amount > available:
            raise ValueError(f"Refund amount exceeds available balance. Available: {available}, Requested: {refund_data.refund_amount}")
        
        refund = DepositRefund(
            deposit_id=deposit_id,
            **refund_data.model_dump(),
            requested_by=requested_by
        )
        self.db.add(refund)
        await self.db.commit()
        await self.db.refresh(refund)
        return refund
    
    async def create_family_deposit(self, deposit_data: FamilyDepositCreate, received_by: str) -> FamilyDeposit:
        """Create a family deposit."""
        # Generate family deposit number
        result = await self.db.execute(select(func.max(FamilyDeposit.id)))
        max_id = result.scalar()
        family_deposit_number = f"FDEP-{datetime.now().strftime('%Y%m%d')}-{(max_id or 0) + 1:04d}"
        
        family_deposit = FamilyDeposit(
            **deposit_data.model_dump(),
            family_deposit_number=family_deposit_number,
            received_by=received_by,
            available_amount=deposit_data.total_amount
        )
        self.db.add(family_deposit)
        await self.db.commit()
        await self.db.refresh(family_deposit)
        return family_deposit
    
    async def add_family_deposit_member(self, family_deposit_id: str, member_data: FamilyDepositMemberCreate) -> FamilyDepositMember:
        """Add a member to family deposit."""
        member = FamilyDepositMember(
            family_deposit_id=family_deposit_id,
            **member_data.model_dump()
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member
    
    async def validate_family_deposit_otp(self, otp_data: FamilyDepositOTPValidate) -> bool:
        """Validate OTP for family deposit usage."""
        result = await self.db.execute(
            select(FamilyDepositOTP).where(
                FamilyDepositOTP.family_deposit_id == otp_data.family_deposit_id,
                FamilyDepositOTP.patient_id == otp_data.patient_id,
                FamilyDepositOTP.otp_code == otp_data.otp_code,
                FamilyDepositOTP.is_used == False,
                FamilyDepositOTP.expires_at > datetime.now(timezone.utc)
            )
        )
        otp = result.scalar_one_or_none()
        
        if not otp:
            return False
        
        # Mark OTP as used
        otp.is_used = True
        otp.used_at = datetime.now(timezone.utc)
        await self.db.commit()
        
        return True
    
    async def get_available_deposit(self, patient_id: str) -> Optional[float]:
        """Get available deposit for a patient."""
        # Check individual deposits
        result = await self.db.execute(
            select(Deposit).where(
                Deposit.patient_id == patient_id,
                Deposit.is_active == True,
                Deposit.is_refundable == True
            )
        )
        deposits = result.scalars().all()
        
        total_available = 0.0
        for deposit in deposits:
            used_result = await self.db.execute(
                select(func.sum(DepositUsage.amount_used)).where(
                    DepositUsage.deposit_id == deposit.id
                )
            )
            used_amount = used_result.scalar() or 0
            total_available += (deposit.amount - used_amount)
        
        # Check family deposits
        result = await self.db.execute(
            select(FamilyDepositMember).where(
                FamilyDepositMember.patient_id == patient_id,
                FamilyDepositMember.is_active == True
            )
        )
        family_memberships = result.scalars().all()
        
        for membership in family_memberships:
            family_deposit = await self.db.get(FamilyDeposit, membership.family_deposit_id)
            if family_deposit and family_deposit.is_active:
                total_available += family_deposit.available_amount
        
        return total_available if total_available > 0 else None
    
    async def transfer_deposit_to_encounter(self, deposit_id: str, encounter_id: str, amount: float, transferred_by: str) -> bool:
        """Transfer deposit to encounter."""
        # Use deposit for the encounter (treat encounter as bill_id for now)
        await self.use_deposit(deposit_id, encounter_id, amount, transferred_by)
        return True
