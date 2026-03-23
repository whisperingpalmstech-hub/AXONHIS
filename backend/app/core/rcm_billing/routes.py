"""Enterprise OPD Billing & Revenue Cycle Engine API Routes"""
import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db

from .models import BillingMaster, BillingService, BillingPayment, BillingDiscount, BillingPayer
from .schemas import (
    TariffMatchQuery, BillingPreviewOut, BillingMasterCreate, BillingMasterOut,
    BillingServiceCreate, BillingServiceOut, BillingDiscountCreate, BillingDiscountOut,
    BillingPaymentCreate, BillingPaymentOut, BillingRefundCreate, BillingRefundOut
)
from .services import (
    PreConsultBillingIntelligence, ServiceBillingEngine, 
    DiscountConcessionRuleEngine, PaymentCollectionEngine, 
    RefundCancellationEngine, FinancialReportingIntegration,
    AutomatedTariffSelectionEngine
)

router = APIRouter(prefix="/rcm-billing", tags=["Enterprise OPD Billing (RCM)"])

# ── 1. Pre-Consult Billing Intelligence ────────────────────────────────────

@router.post("/preview", response_model=BillingPreviewOut)
async def get_billing_cost_preview(query: TariffMatchQuery, db: AsyncSession = Depends(get_db)):
    svc = PreConsultBillingIntelligence(db)
    return await svc.generate_preview(query)

# ── 2 & 3. Create Draft Bill & Connect Services/Payer ─────────────────────

@router.post("/master", response_model=BillingMasterOut)
async def initialize_patient_billing(data: BillingMasterCreate, authorized_user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = ServiceBillingEngine(db)
    # The creator user could be hardcoded for UI testing since auth is bypassed occasionally
    master = await svc.create_draft_bill(data, authorized_user_id)
    # Fetch relations
    return await _fetch_full_bill(master.id, db)

# ── 7. Post-Consult Auto Billing (Appending Services) ─────────────────────

@router.post("/master/{bill_id}/services", response_model=BillingMasterOut)
async def append_service_charge(bill_id: uuid.UUID, data: BillingServiceCreate, db: AsyncSession = Depends(get_db)):
    svc = ServiceBillingEngine(db)
    master = await svc.append_post_consult_service(bill_id, data)
    return await _fetch_full_bill(master.id, db)

# ── 5. Discount & Concession Engine ───────────────────────────────────────

@router.post("/master/{bill_id}/discounts", response_model=BillingMasterOut)
async def apply_bill_discount(bill_id: uuid.UUID, data: BillingDiscountCreate, admin_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = DiscountConcessionRuleEngine(db)
    master = await svc.apply_discount(bill_id, data, admin_id)
    return await _fetch_full_bill(master.id, db)

# ── 6. Payment Collection Engine ──────────────────────────────────────────

@router.post("/master/{bill_id}/payments", response_model=BillingMasterOut)
async def collect_bill_payment(bill_id: uuid.UUID, data: BillingPaymentCreate, cashier_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = PaymentCollectionEngine(db)
    master = await svc.collect_payment(bill_id, data, cashier_id)
    return await _fetch_full_bill(master.id, db)

# ── 9. Refund & Cancellation Engine ───────────────────────────────────────

@router.post("/master/{bill_id}/refunds", response_model=BillingMasterOut)
async def issue_refund_reversal(bill_id: uuid.UUID, data: BillingRefundCreate, auth_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = RefundCancellationEngine(db)
    master = await svc.issue_refund(bill_id, data, auth_id)
    return await _fetch_full_bill(master.id, db)

# ── Fetch Utility ─────────────────────────────────────────────────────────

@router.get("/master/{visit_id}", response_model=BillingMasterOut)
async def get_patient_bill_ledger(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # We query via visit_id primarily for integration
    stmt = select(BillingMaster).where(BillingMaster.visit_id == visit_id)
    m = (await db.execute(stmt)).scalars().first()
    if not m: raise HTTPException(404, "No active bill found for visit.")
    return await _fetch_full_bill(m.id, db)

async def _fetch_full_bill(bill_id: uuid.UUID, db: AsyncSession):
    stmt = (
        select(BillingMaster)
        .where(BillingMaster.id == bill_id)
    )
    master = (await db.execute(stmt)).scalars().first()
    if not master: return None
    
    # We load relations manually for simple serialization bypass if relationship mapping isn't deep loaded
    master.services = list((await db.execute(select(BillingService).where(BillingService.bill_id == bill_id))).scalars().all())
    master.payments = list((await db.execute(select(BillingPayment).where(BillingPayment.bill_id == bill_id))).scalars().all())
    master.discounts = list((await db.execute(select(BillingDiscount).where(BillingDiscount.bill_id == bill_id))).scalars().all())
    master.payer = (await db.execute(select(BillingPayer).where(BillingPayer.bill_id == bill_id))).scalars().first()
    
    return master

# ── 10. Financial Reporting ───────────────────────────────────────────────

@router.get("/analytics/daily-revenue")
async def get_daily_revenue_metrics(db: AsyncSession = Depends(get_db)):
    svc = FinancialReportingIntegration(db)
    return await svc.get_daily_revenue()
