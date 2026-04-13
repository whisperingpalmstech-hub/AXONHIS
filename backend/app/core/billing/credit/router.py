"""Credit Patient Billing Router for Billing Module."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.core.billing.credit.schemas import (
    CreditCompanyCreate, AuthorizationCreate, AuthorizationResponse,
    CoPaySplitCreate, DenialCreate, InvoiceCreate, InvoiceSettlementCreate
)
from app.core.billing.credit.services import CreditBillingService

router = APIRouter()


@router.post("/credit-companies")
async def create_credit_company(
    company_data: CreditCompanyCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new credit company."""
    service = CreditBillingService(db)
    return await service.create_credit_company(company_data)


@router.get("/credit-companies")
async def list_credit_companies(
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List all credit companies."""
    from app.core.billing.credit.models import CreditCompany
    from sqlalchemy import select
    
    query = select(CreditCompany).where(CreditCompany.is_active == is_active)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/authorizations", response_model=AuthorizationResponse)
async def create_authorization(
    auth_data: AuthorizationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create an authorization."""
    service = CreditBillingService(db)
    return await service.create_authorization(auth_data, "system")


@router.get("/authorizations/{authorization_id}/check-limit")
async def check_authorization_limit(
    authorization_id: str,
    amount: float,
    db: AsyncSession = Depends(get_db)
):
    """Check if authorization is within limit."""
    service = CreditBillingService(db)
    is_within_limit = await service.check_authorization_limit(authorization_id, amount)
    return {"authorization_id": authorization_id, "amount": amount, "within_limit": is_within_limit}


@router.post("/bills/{bill_id}/co-pay-split")
async def split_co_pay(
    bill_id: str,
    split_data: CoPaySplitCreate,
    db: AsyncSession = Depends(get_db)
):
    """Split co-pay between patient and company."""
    service = CreditBillingService(db)
    split_data.bill_id = bill_id
    return await service.split_co_pay(split_data)


@router.post("/denials")
async def process_denial(
    denial_data: DenialCreate,
    db: AsyncSession = Depends(get_db)
):
    """Process a denial."""
    service = CreditBillingService(db)
    return await service.process_denial(denial_data)


@router.post("/invoices")
async def generate_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Generate an invoice for credit billing."""
    service = CreditBillingService(db)
    return await service.generate_invoice(invoice_data)


@router.post("/invoices/{invoice_id}/settle")
async def settle_invoice(
    invoice_id: str,
    settlement_data: InvoiceSettlementCreate,
    db: AsyncSession = Depends(get_db)
):
    """Settle an invoice."""
    service = CreditBillingService(db)
    return await service.settle_invoice(invoice_id, settlement_data)


@router.post("/patients/{patient_id}/security-deposit-adjust")
async def adjust_security_deposit(
    patient_id: str,
    adjustment_amount: float,
    db: AsyncSession = Depends(get_db)
):
    """Adjust security deposit for credit billing."""
    service = CreditBillingService(db)
    success = await service.adjust_security_deposit(patient_id, adjustment_amount)
    if not success:
        raise HTTPException(status_code=404, detail="Security deposit not found")
    return {"success": True}
