"""Contract Management Router for Billing Module."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.core.billing.contracts.schemas import (
    ContractCreate, ContractUpdate, ContractInclusionCreate, ContractExclusionCreate,
    ContractCoPayCreate, ContractCAPCreate, ContractCreditLimitCreate,
    ContractPaymentTermsCreate, ContractPackageCreate, ContractEmployeeGradeCreate,
    PatientCreditAssignmentCreate
)
from app.core.billing.contracts.services import ContractService

router = APIRouter()


@router.post("/contracts")
async def create_contract(
    contract_data: ContractCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new contract."""
    service = ContractService(db)
    return await service.create_contract(contract_data)


@router.get("/contracts")
async def list_contracts(
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List all contracts."""
    from app.core.billing.contracts.models import Contract
    from sqlalchemy import select
    
    query = select(Contract).where(Contract.is_active == is_active)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/contracts/{contract_id}")
async def get_contract(contract_id: str, db: AsyncSession = Depends(get_db)):
    """Get contract details."""
    from app.core.billing.contracts.models import Contract
    
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.post("/contracts/{contract_id}/inclusions")
async def add_contract_inclusion(
    contract_id: str,
    inclusion_data: ContractInclusionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a service to contract inclusions."""
    service = ContractService(db)
    return await service.add_contract_inclusion(contract_id, inclusion_data)


@router.post("/contracts/{contract_id}/exclusions")
async def add_contract_exclusion(
    contract_id: str,
    exclusion_data: ContractExclusionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a service to contract exclusions."""
    service = ContractService(db)
    return await service.add_contract_exclusion(contract_id, exclusion_data)


@router.post("/contracts/{contract_id}/co-pay")
async def set_co_pay(
    contract_id: str,
    copay_data: ContractCoPayCreate,
    db: AsyncSession = Depends(get_db)
):
    """Set co-pay configuration."""
    service = ContractService(db)
    return await service.set_co_pay(contract_id, copay_data)


@router.post("/contracts/{contract_id}/cap")
async def set_cap_amount(
    contract_id: str,
    cap_data: ContractCAPCreate,
    db: AsyncSession = Depends(get_db)
):
    """Set CAP amount configuration."""
    service = ContractService(db)
    return await service.set_cap_amount(contract_id, cap_data)


@router.post("/contracts/{contract_id}/credit-limit")
async def set_credit_limit(
    contract_id: str,
    credit_data: ContractCreditLimitCreate,
    db: AsyncSession = Depends(get_db)
):
    """Set credit limit configuration."""
    service = ContractService(db)
    return await service.set_credit_limit(contract_id, credit_data)


@router.post("/contracts/{contract_id}/payment-terms")
async def set_payment_terms(
    contract_id: str,
    terms_data: ContractPaymentTermsCreate,
    db: AsyncSession = Depends(get_db)
):
    """Set payment terms."""
    service = ContractService(db)
    return await service.set_payment_terms(contract_id, terms_data)


@router.post("/contracts/{contract_id}/packages")
async def add_package_to_contract(
    contract_id: str,
    package_data: ContractPackageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a package to contract."""
    service = ContractService(db)
    return await service.add_package_to_contract(contract_id, package_data)


@router.post("/contracts/{contract_id}/employee-grades")
async def add_employee_grade(
    contract_id: str,
    grade_data: ContractEmployeeGradeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add employee grade contract."""
    service = ContractService(db)
    return await service.add_employee_grade(contract_id, grade_data)


@router.post("/patients/{patient_id}/assign-credit")
async def assign_credit_company(
    patient_id: str,
    assignment_data: PatientCreditAssignmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Assign patient to credit company."""
    service = ContractService(db)
    return await service.assign_credit_company(assignment_data, "system")


@router.get("/patients/{patient_id}/contract-applicability")
async def get_contract_applicability(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Get contract applicability for a patient."""
    service = ContractService(db)
    applicability = await service.get_contract_applicability(patient_id)
    if not applicability:
        raise HTTPException(status_code=404, detail="No contract found for this patient")
    return applicability
