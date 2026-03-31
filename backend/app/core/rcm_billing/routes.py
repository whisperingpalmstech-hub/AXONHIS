"""Enterprise OPD Billing & Revenue Cycle Engine API Routes"""
import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db

from .models import BillingMaster, BillingService, BillingPayment, BillingDiscount, BillingPayer, BillingTariff
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
from app.dependencies import CurrentUser

router = APIRouter(prefix="/rcm-billing", tags=["Enterprise OPD Billing (RCM)"])

# ── 1. Pre-Consult Billing Intelligence ────────────────────────────────────

@router.post("/preview", response_model=BillingPreviewOut)
async def get_billing_cost_preview(query: TariffMatchQuery, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = PreConsultBillingIntelligence(db)
    return await svc.generate_preview(query, org_id=user.org_id)

# ── 2 & 3. Create Draft Bill & Connect Services/Payer ─────────────────────

@router.post("/master", response_model=BillingMasterOut)
async def initialize_patient_billing(data: BillingMasterCreate, authorized_user_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = ServiceBillingEngine(db)
    # Use org_id from the authenticated session
    master = await svc.create_draft_bill(data, authorized_user_id, org_id=user.org_id)
    # Fetch relations
    return await _fetch_full_bill(master.id, db, org_id=user.org_id)

# ── 7. Post-Consult Auto Billing (Appending Services) ─────────────────────

@router.post("/master/{bill_id}/services", response_model=BillingMasterOut)
async def append_service_charge(bill_id: uuid.UUID, data: BillingServiceCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = ServiceBillingEngine(db)
    master = await svc.append_post_consult_service(bill_id, data, org_id=user.org_id)
    return await _fetch_full_bill(master.id, db, org_id=user.org_id)

# ── 5. Discount & Concession Engine ───────────────────────────────────────

@router.post("/master/{bill_id}/discounts", response_model=BillingMasterOut)
async def apply_bill_discount(bill_id: uuid.UUID, data: BillingDiscountCreate, admin_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = DiscountConcessionRuleEngine(db)
    master = await svc.apply_discount(bill_id, data, admin_id, org_id=user.org_id)
    return await _fetch_full_bill(master.id, db, org_id=user.org_id)

# ── 6. Payment Collection Engine ──────────────────────────────────────────

@router.post("/master/{bill_id}/payments", response_model=BillingMasterOut)
async def collect_bill_payment(bill_id: uuid.UUID, data: BillingPaymentCreate, cashier_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = PaymentCollectionEngine(db)
    master = await svc.collect_payment(bill_id, data, cashier_id, org_id=user.org_id)
    return await _fetch_full_bill(master.id, db, org_id=user.org_id)

# ── 9. Refund & Cancellation Engine ───────────────────────────────────────

@router.post("/master/{bill_id}/refunds", response_model=BillingMasterOut)
async def issue_refund_reversal(bill_id: uuid.UUID, data: BillingRefundCreate, auth_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = RefundCancellationEngine(db)
    master = await svc.issue_refund(bill_id, data, auth_id, org_id=user.org_id)
    return await _fetch_full_bill(master.id, db, org_id=user.org_id)

# ── Fetch Utility ─────────────────────────────────────────────────────────

@router.get("/master/{visit_id}", response_model=BillingMasterOut)
async def get_patient_bill_ledger(visit_id: uuid.UUID, user: CurrentUser, patient_id: uuid.UUID = None, db: AsyncSession = Depends(get_db)):
    """Fetch the master bill for a specific visit and patient. 
    Added patient_id filter to prevent data leakage between different patients sharing a generic visit_id."""
    # Build query with dual filters + org isolation
    stmt = select(BillingMaster).where(
        BillingMaster.visit_id == visit_id,
        BillingMaster.org_id == user.org_id
    )
    if patient_id:
        stmt = stmt.where(BillingMaster.patient_id == patient_id)
    
    # Pick the most recent one if multiple exist (unlikely in prod, but common in test data)
    stmt = stmt.order_by(BillingMaster.generated_at.desc())
    
    m = (await db.execute(stmt)).scalars().first()
    if not m: raise HTTPException(404, "No active bill found for this patient/visit combination in your organization.")
    return await _fetch_full_bill(m.id, db, org_id=user.org_id)

async def _fetch_full_bill(bill_id: uuid.UUID, db: AsyncSession, org_id: uuid.UUID = None):
    stmt = (
        select(BillingMaster)
        .where(BillingMaster.id == bill_id)
    )
    if org_id:
        stmt = stmt.where(BillingMaster.org_id == org_id)
    master = (await db.execute(stmt)).scalars().first()
    if not master: return None
    
    # We load relations manually for simple serialization bypass if relationship mapping isn't deep loaded
    master.services = list((await db.execute(select(BillingService).where(BillingService.bill_id == bill_id))).scalars().all())
    master.payments = list((await db.execute(select(BillingPayment).where(BillingPayment.bill_id == bill_id))).scalars().all())
    master.discounts = list((await db.execute(select(BillingDiscount).where(BillingDiscount.bill_id == bill_id))).scalars().all())
    master.payer = (await db.execute(select(BillingPayer).where(BillingPayer.bill_id == bill_id))).scalars().first()
    
    return master

# ── Encounter-Based Auto-Billing ─────────────────────────────────────────

@router.get("/encounter-charges/{patient_id}")
async def get_encounter_auto_charges(patient_id: uuid.UUID, user: CurrentUser, encounter_id: str = None, db: AsyncSession = Depends(get_db)):
    """Auto-aggregate all charges for a patient from their encounter (lab, pharmacy, consultation).
    This replaces the need for manual service entry in billing."""
    from app.core.encounter_bridge import EncounterBridgeService
    bridge = EncounterBridgeService(db)
    enc_uuid = uuid.UUID(encounter_id) if encounter_id else None
    charges = await bridge.get_encounter_charges(patient_id, enc_uuid)
    return {"patient_id": str(patient_id), "charges": charges, "total_items": len(charges)}

# ── 10. Financial Reporting ───────────────────────────────────────────────

@router.post("/tariffs/seed")
async def seed_hospital_tariffs(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    """Seed standard hospital tariffs for testing. Isolated to the current organization."""
    from decimal import Decimal
    from sqlalchemy import select, func
    
    # Check if tariffs already exist to avoid duplication within org
    count = (await db.execute(select(func.count()).select_from(BillingTariff).where(BillingTariff.org_id == user.org_id))).scalar()
    if count and count > 0:
        return {"status": "ok", "message": "Tariffs already seeded", "count": count}
    
    tariffs = [
        # OPD Services
        {"service_name": "OPD Consultation Fee", "tariff_category": "standard", "price": Decimal("500.00")},
        {"service_name": "General Consultation", "tariff_category": "standard", "price": Decimal("500.00")},
        {"service_name": "Specialist Consultation", "tariff_category": "standard", "price": Decimal("1000.00")},
        {"service_name": "Emergency Consultation", "tariff_category": "standard", "price": Decimal("1500.00")},
        
        # Lab Tests
        {"service_name": "CBC with Differential", "tariff_category": "standard", "price": Decimal("350.00")},
        {"service_name": "Comprehensive Metabolic Panel (CMP)", "tariff_category": "standard", "price": Decimal("800.00")},
        {"service_name": "CRP (C-Reactive Protein)", "tariff_category": "standard", "price": Decimal("450.00")},
        {"service_name": "Troponin I", "tariff_category": "standard", "price": Decimal("900.00")},
        {"service_name": "CK-MB", "tariff_category": "standard", "price": Decimal("600.00")},
        {"service_name": "Lipid Panel", "tariff_category": "standard", "price": Decimal("500.00")},
        {"service_name": "Urine Routine", "tariff_category": "standard", "price": Decimal("200.00")},
        {"service_name": "Serum Creatinine", "tariff_category": "standard", "price": Decimal("250.00")},
        {"service_name": "Blood Urea Nitrogen", "tariff_category": "standard", "price": Decimal("200.00")},
        {"service_name": "Serum Electrolytes", "tariff_category": "standard", "price": Decimal("400.00")},
        {"service_name": "Urine Culture", "tariff_category": "standard", "price": Decimal("550.00")},
        {"service_name": "CBC Diagnostics", "tariff_category": "standard", "price": Decimal("350.00")},
        
        # Radiology / Imaging
        {"service_name": "PA Chest X-Ray", "tariff_category": "standard", "price": Decimal("400.00")},
        {"service_name": "12-Lead ECG", "tariff_category": "standard", "price": Decimal("300.00")},
        {"service_name": "Echocardiogram", "tariff_category": "standard", "price": Decimal("2500.00")},
        {"service_name": "Ultrasound KUB", "tariff_category": "standard", "price": Decimal("1200.00")},
        {"service_name": "CT KUB", "tariff_category": "standard", "price": Decimal("3500.00")},
        {"service_name": "MRI Brain", "tariff_category": "standard", "price": Decimal("6000.00")},
        {"service_name": "X-Ray KUB", "tariff_category": "standard", "price": Decimal("500.00")},
        
        # Pharmacy / Medications
        {"service_name": "Rx: Diclofenac Injection STAT", "tariff_category": "standard", "price": Decimal("150.00")},
        {"service_name": "Rx: Tamsulosin 0.4mg", "tariff_category": "standard", "price": Decimal("120.00")},
        {"service_name": "Rx: Paracetamol 500 mg", "tariff_category": "standard", "price": Decimal("30.00")},
        {"service_name": "Rx: Amoxicillin 500 mg", "tariff_category": "standard", "price": Decimal("80.00")},
        {"service_name": "Rx: Generic Medicine Standard", "tariff_category": "standard", "price": Decimal("100.00")},
        
        # Procedures
        {"service_name": "IV Cannulation", "tariff_category": "standard", "price": Decimal("200.00")},
        {"service_name": "Wound Dressing", "tariff_category": "standard", "price": Decimal("300.00")},
        {"service_name": "Nebulization", "tariff_category": "standard", "price": Decimal("150.00")},
        
        # Corporate tariffs (10% discount)
        {"service_name": "OPD Consultation Fee", "tariff_category": "corporate", "price": Decimal("450.00")},
        {"service_name": "General Consultation", "tariff_category": "corporate", "price": Decimal("450.00")},
    ]
    
    for t_data in tariffs:
        tariff = BillingTariff(**t_data, is_active=True, org_id=user.org_id)
        db.add(tariff)
    
    await db.commit()
    return {"status": "ok", "tariffs_seeded": len(tariffs)}

@router.get("/analytics/daily-revenue")
async def get_daily_revenue_metrics(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = FinancialReportingIntegration(db)
    return await svc.get_daily_revenue(org_id=user.org_id)
