import uuid
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

from .schemas import BillingRecordCreate, BillingRecordOut, DiscountCreate, DiscountOut, PaymentCreate, PaymentOut, RefundCreate, RefundOut, ReportGenerate, ReportOut
from .services import BillingReportingComplianceService

router = APIRouter()

# 1. Billing Transaction Management
@router.post("/bills", response_model=BillingRecordOut, status_code=201)
async def generate_bill(
    payload: BillingRecordCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Generate OP/IP pharmacy bill accounting for tax and items."""
    user_id = uuid.uuid4()
    svc = BillingReportingComplianceService(db)
    return await svc.create_billing_record(payload, user_id)

@router.get("/bills", response_model=List[BillingRecordOut])
async def check_billing_history(
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve outstanding or consolidated bill records."""
    svc = BillingReportingComplianceService(db)
    return await svc.list_open_bills()

# 2. Discount Processing
@router.post("/discounts", response_model=DiscountOut, status_code=201)
async def map_concession(
    payload: DiscountCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Approve and apply dynamic discounting bounds (Staff, Promo)."""
    user_id = uuid.uuid4()
    svc = BillingReportingComplianceService(db)
    return await svc.authorize_discount(payload, user_id)

# 3. Payment Processing
@router.post("/payments", response_model=PaymentOut, status_code=201)
async def capture_payment_transaction(
    payload: PaymentCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Log actual capital incoming against Bill Records creating Receipts."""
    cashier_id = uuid.uuid4()
    svc = BillingReportingComplianceService(db)
    return await svc.process_payment(payload, cashier_id)

# 4. Refund Engine 
@router.post("/refunds", response_model=RefundOut, status_code=201)
async def request_bill_refund(
    payload: RefundCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Issue valid Refunds/Credit Notes for returns mapping across Txns."""
    auth_user = uuid.uuid4()
    svc = BillingReportingComplianceService(db)
    return await svc.issue_refund(payload, auth_user)

# 5. Financial Reporting & Analytics (Revenue & Compliance)
@router.post("/reports", response_model=ReportOut, status_code=201)
async def synthesize_reporting_engine(
    payload: ReportGenerate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Generate multi-format revenue sheets and regulatory audits (Narcotics compliance)."""
    gen_user = uuid.uuid4()
    svc = BillingReportingComplianceService(db)
    return await svc.generate_report(payload, gen_user)
