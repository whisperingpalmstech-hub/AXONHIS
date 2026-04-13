"""Credit Patient Billing Services for Billing Module."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.core.billing.credit.models import (
    CreditCompany, Authorization, CoPaySplit, Denial,
    Invoice, InvoiceSettlement
)
from app.core.billing.credit.schemas import (
    CreditCompanyCreate, AuthorizationCreate, CoPaySplitCreate,
    DenialCreate, InvoiceCreate, InvoiceSettlementCreate
)


class CreditBillingService:
    """Service for credit patient billing operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_credit_company(self, company_data: CreditCompanyCreate) -> CreditCompany:
        """Create a new credit company."""
        company = CreditCompany(**company_data.model_dump())
        self.db.add(company)
        await self.db.commit()
        await self.db.refresh(company)
        return company
    
    async def create_authorization(self, auth_data: AuthorizationCreate, created_by: str) -> Authorization:
        """Create an authorization."""
        # Generate authorization number
        result = await self.db.execute(select(func.max(Authorization.id)))
        max_id = result.scalar()
        auth_number = f"AUTH-{datetime.now().strftime('%Y%m%d')}-{(max_id or 0) + 1:04d}"
        
        authorization = Authorization(
            **auth_data.model_dump(),
            authorization_number=auth_number,
            created_by=created_by
        )
        self.db.add(authorization)
        await self.db.commit()
        await self.db.refresh(authorization)
        return authorization
    
    async def check_authorization_limit(self, authorization_id: str, amount: float) -> bool:
        """Check if authorization is within limit."""
        auth = await self.db.get(Authorization, authorization_id)
        if not auth or auth.status != "active":
            return False
        
        # Check if authorization is still valid
        now = datetime.now(timezone.utc)
        if auth.valid_from and now < auth.valid_from:
            return False
        if auth.valid_to and now > auth.valid_to:
            return False
        
        # Check if amount is within limit
        available = auth.authorized_amount - auth.used_amount
        return amount <= available
    
    async def split_co_pay(self, split_data: CoPaySplitCreate) -> CoPaySplit:
        """Split co-pay between patient and company."""
        # Get contract to determine co-pay percentage
        from app.core.billing.contracts.models import ContractCoPay
        result = await self.db.execute(
            select(ContractCoPay).where(
                ContractCoPay.contract_id == split_data.contract_id,
                ContractCoPay.is_active == True
            )
        )
        copay_config = result.scalar_one_or_none()
        
        if copay_config:
            copay_percentage = copay_config.copay_percentage or split_data.copay_percentage or 0
        else:
            copay_percentage = split_data.copay_percentage or 0
        
        # Calculate shares
        company_share = split_data.total_amount * (copay_percentage / 100)
        patient_share = split_data.total_amount - company_share
        
        split = CoPaySplit(
            **split_data.model_dump(),
            patient_share=patient_share,
            company_share=company_share,
            copay_percentage=copay_percentage
        )
        self.db.add(split)
        await self.db.commit()
        await self.db.refresh(split)
        return split
    
    async def process_denial(self, denial_data: DenialCreate) -> Denial:
        """Process a denial."""
        denial = Denial(**denial_data.model_dump())
        self.db.add(denial)
        await self.db.commit()
        await self.db.refresh(denial)
        return denial
    
    async def generate_invoice(self, invoice_data: InvoiceCreate) -> Invoice:
        """Generate an invoice for credit billing."""
        # Generate invoice number
        result = await self.db.execute(select(func.max(Invoice.id)))
        max_id = result.scalar()
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{(max_id or 0) + 1:04d}"
        
        # Calculate total amount from bills
        total_amount = 0.0
        # In a real implementation, you would calculate from actual bills
        # For now, use the provided amount or calculate from bill_ids
        
        invoice = Invoice(
            invoice_number=invoice_number,
            **invoice_data.model_dump(),
            total_amount=total_amount
        )
        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice
    
    async def settle_invoice(self, invoice_id: str, settlement_data: InvoiceSettlementCreate) -> InvoiceSettlement:
        """Settle an invoice."""
        settlement = InvoiceSettlement(
            invoice_id=invoice_id,
            **settlement_data.model_dump()
        )
        self.db.add(settlement)
        
        # Update invoice status
        invoice = await self.db.get(Invoice, invoice_id)
        if invoice:
            invoice.paid_amount += settlement.settlement_amount
            if invoice.paid_amount >= invoice.total_amount:
                invoice.status = "settled"
            elif invoice.paid_amount > 0:
                invoice.status = "partial"
        
        await self.db.commit()
        await self.db.refresh(settlement)
        return settlement
    
    async def adjust_security_deposit(self, patient_id: str, adjustment_amount: float) -> bool:
        """Adjust security deposit for credit billing."""
        # Get patient's security deposit
        from app.core.billing.deposits.models import Deposit, DepositUsage
        result = await self.db.execute(
            select(Deposit).where(
                Deposit.patient_id == patient_id,
                Deposit.deposit_type == "security",
                Deposit.is_active == True
            )
        )
        deposit = result.scalar_one_or_none()
        
        if not deposit:
            return False
        
        # Create a deposit usage entry for the adjustment
        usage = DepositUsage(
            deposit_id=deposit.id,
            bill_id=None,  # Security deposit adjustment
            amount_used=adjustment_amount,
            used_by="system"
        )
        self.db.add(usage)
        await self.db.commit()
        return True
