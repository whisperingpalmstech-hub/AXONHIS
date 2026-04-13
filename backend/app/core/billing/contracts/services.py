"""Contract Management Services for Billing Module."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.core.billing.contracts.models import (
    Contract, ContractInclusion, ContractExclusion, ContractCoPay,
    ContractCAP, ContractCreditLimit, ContractPaymentTerms,
    ContractPackage, ContractEmployeeGrade, PatientCreditAssignment
)
from app.core.billing.contracts.schemas import (
    ContractCreate, ContractUpdate, ContractInclusionCreate, ContractExclusionCreate,
    ContractCoPayCreate, ContractCAPCreate, ContractCreditLimitCreate,
    ContractPaymentTermsCreate, ContractPackageCreate, ContractEmployeeGradeCreate,
    PatientCreditAssignmentCreate
)


class ContractService:
    """Service for contract management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_contract(self, contract_data: ContractCreate) -> Contract:
        """Create a new contract."""
        contract = Contract(**contract_data.model_dump())
        self.db.add(contract)
        await self.db.commit()
        await self.db.refresh(contract)
        return contract
    
    async def add_contract_inclusion(self, contract_id: str, inclusion_data: ContractInclusionCreate) -> ContractInclusion:
        """Add a service to contract inclusions."""
        inclusion = ContractInclusion(
            contract_id=contract_id,
            **inclusion_data.model_dump()
        )
        self.db.add(inclusion)
        await self.db.commit()
        await self.db.refresh(inclusion)
        return inclusion
    
    async def add_contract_exclusion(self, contract_id: str, exclusion_data: ContractExclusionCreate) -> ContractExclusion:
        """Add a service to contract exclusions."""
        exclusion = ContractExclusion(
            contract_id=contract_id,
            **exclusion_data.model_dump()
        )
        self.db.add(exclusion)
        await self.db.commit()
        await self.db.refresh(exclusion)
        return exclusion
    
    async def set_co_pay(self, contract_id: str, copay_data: ContractCoPayCreate) -> ContractCoPay:
        """Set co-pay configuration."""
        copay = ContractCoPay(
            contract_id=contract_id,
            **copay_data.model_dump()
        )
        self.db.add(copay)
        await self.db.commit()
        await self.db.refresh(copay)
        return copay
    
    async def set_cap_amount(self, contract_id: str, cap_data: ContractCAPCreate) -> ContractCAP:
        """Set CAP amount configuration."""
        cap = ContractCAP(
            contract_id=contract_id,
            **cap_data.model_dump()
        )
        self.db.add(cap)
        await self.db.commit()
        await self.db.refresh(cap)
        return cap
    
    async def set_credit_limit(self, contract_id: str, credit_data: ContractCreditLimitCreate) -> ContractCreditLimit:
        """Set credit limit configuration."""
        credit_limit = ContractCreditLimit(
            contract_id=contract_id,
            credit_limit=credit_data.credit_limit,
            used_credit=0,
            available_credit=credit_data.credit_limit,
            reset_period=credit_data.reset_period,
            is_active=credit_data.is_active
        )
        self.db.add(credit_limit)
        await self.db.commit()
        await self.db.refresh(credit_limit)
        return credit_limit
    
    async def set_payment_terms(self, contract_id: str, terms_data: ContractPaymentTermsCreate) -> ContractPaymentTerms:
        """Set payment terms."""
        payment_terms = ContractPaymentTerms(
            contract_id=contract_id,
            **terms_data.model_dump()
        )
        self.db.add(payment_terms)
        await self.db.commit()
        await self.db.refresh(payment_terms)
        return payment_terms
    
    async def add_package_to_contract(self, contract_id: str, package_data: ContractPackageCreate) -> ContractPackage:
        """Add a package to contract."""
        package = ContractPackage(
            contract_id=contract_id,
            **package_data.model_dump()
        )
        self.db.add(package)
        await self.db.commit()
        await self.db.refresh(package)
        return package
    
    async def add_employee_grade(self, contract_id: str, grade_data: ContractEmployeeGradeCreate) -> ContractEmployeeGrade:
        """Add employee grade contract."""
        grade = ContractEmployeeGrade(
            contract_id=contract_id,
            **grade_data.model_dump()
        )
        self.db.add(grade)
        await self.db.commit()
        await self.db.refresh(grade)
        return grade
    
    async def assign_credit_company(self, assignment_data: PatientCreditAssignmentCreate, assigned_by: str) -> PatientCreditAssignment:
        """Assign patient to credit company."""
        assignment = PatientCreditAssignment(
            **assignment_data.model_dump(),
            assigned_by=assigned_by
        )
        self.db.add(assignment)
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment
    
    async def get_contract_applicability(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get contract applicability for a patient."""
        result = await self.db.execute(
            select(PatientCreditAssignment).where(
                PatientCreditAssignment.patient_id == patient_id,
                PatientCreditAssignment.is_active == True
            )
        )
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            return None
        
        contract = await self.db.get(Contract, assignment.contract_id)
        if not contract or not contract.is_active:
            return None
        
        return {
            "contract_id": str(contract.id),
            "contract_name": contract.contract_name,
            "contract_type": contract.contract_type,
            "company_name": contract.company_name,
            "employee_id": assignment.employee_id,
            "employee_grade": assignment.employee_grade
        }
    
    async def validate_contract_authorization(self, contract_id: str, amount: float) -> bool:
        """Validate if authorization is within credit limit."""
        result = await self.db.execute(
            select(ContractCreditLimit).where(
                ContractCreditLimit.contract_id == contract_id,
                ContractCreditLimit.is_active == True
            )
        )
        credit_limit = result.scalar_one_or_none()
        
        if not credit_limit:
            return True  # No credit limit set
        
        available_credit = credit_limit.available_credit - credit_limit.used_credit
        return amount <= available_credit
