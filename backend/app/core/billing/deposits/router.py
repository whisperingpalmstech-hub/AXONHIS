"""Deposit Management Router for Billing Module."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.core.billing.deposits.schemas import (
    DepositCreate, DepositResponse, DepositRefundCreate, DepositRefundResponse,
    FamilyDepositCreate, FamilyDepositMemberCreate, FamilyDepositOTPValidate
)
from app.core.billing.deposits.services import DepositService

router = APIRouter()


@router.post("/deposits", response_model=DepositResponse)
async def create_deposit(
    deposit_data: DepositCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new deposit."""
    service = DepositService(db)
    return await service.create_deposit(deposit_data, "system")


@router.get("/deposits", response_model=List[DepositResponse])
async def list_deposits(
    patient_id: str = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List deposits."""
    from app.core.billing.deposits.models import Deposit
    from sqlalchemy import select
    
    query = select(Deposit).where(Deposit.is_active == is_active)
    if patient_id:
        query = query.where(Deposit.patient_id == patient_id)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/deposits/{deposit_id}", response_model=DepositResponse)
async def get_deposit(deposit_id: str, db: AsyncSession = Depends(get_db)):
    """Get deposit details."""
    from app.core.billing.deposits.models import Deposit
    
    deposit = await db.get(Deposit, deposit_id)
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    return deposit


@router.post("/deposits/{deposit_id}/use")
async def use_deposit(
    deposit_id: str,
    bill_id: str,
    amount: float,
    db: AsyncSession = Depends(get_db)
):
    """Use deposit for a bill."""
    service = DepositService(db)
    return await service.use_deposit(deposit_id, bill_id, amount, "system")


@router.post("/deposits/{deposit_id}/refund", response_model=DepositRefundResponse)
async def refund_deposit(
    deposit_id: str,
    refund_data: DepositRefundCreate,
    db: AsyncSession = Depends(get_db)
):
    """Process a refund request."""
    service = DepositService(db)
    return await service.refund_deposit(deposit_id, refund_data, "system")


@router.post("/family-deposits")
async def create_family_deposit(
    deposit_data: FamilyDepositCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a family deposit."""
    service = DepositService(db)
    return await service.create_family_deposit(deposit_data, "system")


@router.post("/family-deposits/{family_deposit_id}/members")
async def add_family_deposit_member(
    family_deposit_id: str,
    member_data: FamilyDepositMemberCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a member to family deposit."""
    service = DepositService(db)
    return await service.add_family_deposit_member(family_deposit_id, member_data)


@router.post("/family-deposits/validate-otp")
async def validate_family_deposit_otp(
    otp_data: FamilyDepositOTPValidate,
    db: AsyncSession = Depends(get_db)
):
    """Validate OTP for family deposit usage."""
    service = DepositService(db)
    is_valid = await service.validate_family_deposit_otp(otp_data)
    return {"valid": is_valid}


@router.get("/patients/{patient_id}/deposits")
async def get_patient_deposits(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Get available deposit for a patient."""
    service = DepositService(db)
    available = await service.get_available_deposit(patient_id)
    return {"patient_id": patient_id, "available_deposit": available}
