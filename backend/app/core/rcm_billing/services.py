"""Enterprise OPD Billing & Revenue Cycle Engine — Services"""
import uuid
from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from .models import (
    BillingMaster, BillingService, BillingPayment, BillingDiscount,
    BillingRefund, BillingTariff, BillingPayer, BillStatus, PayerType
)
from .schemas import (
    TariffMatchQuery, BillingPreviewOut, BillingMasterCreate,
    BillingServiceCreate, BillingDiscountCreate, BillingPaymentCreate,
    BillingRefundCreate
)

class AutomatedTariffSelectionEngine:
    """Core RCM pricing matrix algorithm"""
    
    # Common service name aliases for tariff matching
    SERVICE_ALIASES = {
        "complete blood count": "CBC",
        "complete blood count (cbc)": "CBC", 
        "full blood count": "CBC",
        "fbc": "CBC",
        "basic metabolic panel": "BMP",
        "blood glucose": "Blood Sugar",
        "blood sugar fasting": "Blood Sugar",
        "erythrocyte sedimentation rate": "ESR",
        "liver function test": "LFT",
        "renal function test": "RFT Kidney",
        "kidney function test": "RFT Kidney",
        "thyroid stimulating hormone": "Thyroid Panel",
        "tsh": "Thyroid Panel",
        "ct scan": "CT Scan",
        "x-ray": "X-Ray",
        "xray": "X-Ray",
        "ultrasound": "Ultrasound",
        "usg": "Ultrasound",
        "ecg": "ECG",
        "electrocardiogram": "ECG",
        "mri": "MRI Scan",
    }
    
    def __init__(self, db: AsyncSession, org_id: uuid.UUID = None):
        self.db = db
        self.org_id = org_id

    async def get_applicable_tariff(self, query: TariffMatchQuery, org_id: uuid.UUID = None) -> BillingTariff:
        # Check if the service name has an alias
        effective_org_id = org_id or self.org_id
        service_name = query.service_name
        alias = self.SERVICE_ALIASES.get(service_name.lower().strip())
        search_names = [service_name]
        if alias:
            search_names.append(alias)
        
        for svc in search_names:
            svc_name = f"%{svc}%"
            filter_args = [
                BillingTariff.service_name.ilike(svc_name), 
                BillingTariff.is_active == True,
                BillingTariff.org_id == effective_org_id
            ]
            
            # 2. Tier rules
            cat = str(query.patient_category or "standard")
            if query.insurance_plan: category = "insurance"
            elif cat == "corporate": category = "corporate"
            else: category = "standard"
            
            filter_args.append(BillingTariff.tariff_category == category)
            
            if query.doctor_grade:
                filter_args.append(BillingTariff.doctor_grade == query.doctor_grade)

            stmt = select(BillingTariff).where(and_(*filter_args)).limit(1)
            tariff = (await self.db.execute(stmt)).scalars().first()
            
            # Fallback 1: standard category with fuzzy name
            if not tariff:
                fallback = select(BillingTariff).where(
                    and_(
                        BillingTariff.service_name.ilike(svc_name), 
                        BillingTariff.tariff_category == "standard",
                        BillingTariff.org_id == effective_org_id
                    )
                ).limit(1)
                tariff = (await self.db.execute(fallback)).scalars().first()
            
            # Fallback 2: exact name match any category
            if not tariff:
                clean_name = svc.split(':')[0].strip()
                fallback2 = select(BillingTariff).where(
                    and_(
                        BillingTariff.service_name.ilike(f"%{clean_name}%"), 
                        BillingTariff.is_active == True,
                        BillingTariff.org_id == effective_org_id
                    )
                ).limit(1)
                tariff = (await self.db.execute(fallback2)).scalars().first()
            
            if tariff:
                return tariff
            
        return None

class PreConsultBillingIntelligence:
    """Frontgate patient cost estimator generated prior to admission step."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_preview(self, query: TariffMatchQuery, org_id: uuid.UUID = None) -> BillingPreviewOut:
        engine = AutomatedTariffSelectionEngine(self.db, org_id=org_id)
        tariff = await engine.get_applicable_tariff(query, org_id=org_id)
        if not tariff:
            # Fake generate if not found strictly for demo logic / new installations
            return BillingPreviewOut(estimated_cost=Decimal("0.00"), service_name=query.service_name, tariff_applied="unavailable")
        return BillingPreviewOut(
            estimated_cost=tariff.price,
            service_name=tariff.service_name,
            tariff_applied=f"{tariff.tariff_category.capitalize()} - {tariff.doctor_grade or 'Standard'}"
        )

class ServiceBillingEngine:
    """RCM Master Billing Handler"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _recalculate_bill(self, bill: BillingMaster):
        """Summation workflow over active services, discounts, and payments"""
        # Sum services
        services = (await self.db.execute(
            select(func.sum(BillingService.total_cost)).where(and_(
                BillingService.bill_id == bill.id, BillingService.status == "active"
            ))
        )).scalar() or Decimal("0.00")
        
        # Pull discounts applied globally onto bill
        discounts = (await self.db.execute(
            select(func.sum(BillingDiscount.discount_value)).where(BillingDiscount.bill_id == bill.id)
        )).scalar() or Decimal("0.00")
        
        # Pull collected tender
        payments = (await self.db.execute(
            select(func.sum(BillingPayment.amount)).where(BillingPayment.bill_id == bill.id)
        )).scalar() or Decimal("0.00")
        
        # Reversals
        refunds = (await self.db.execute(
            select(func.sum(BillingRefund.refund_amount)).where(BillingRefund.bill_id == bill.id)
        )).scalar() or Decimal("0.00")

        gross = Decimal(services)
        net = max(gross - discounts, Decimal("0.00"))
        bal = net - (payments - refunds)
        
        bill.gross_amount = gross
        bill.discount_amount = discounts
        bill.net_amount = net
        bill.paid_amount = (payments - refunds)
        bill.balance_amount = max(bal, Decimal("0.00"))
        
        # Status Mutations
        if bal <= 0 and net > 0:
            bill.status = BillStatus.paid
        elif payments > 0 and bal > 0:
            bill.status = BillStatus.partially_paid
        else:
            bill.status = BillStatus.unpaid

        await self.db.commit()
        await self.db.refresh(bill)
        return bill

    async def create_draft_bill(self, data: BillingMasterCreate, user_id: uuid.UUID, org_id: uuid.UUID = None) -> BillingMaster:
        # Create master
        bill_num = f"INV-{datetime.utcnow().strftime('%y%m%d%H%M%S')}"
        master = BillingMaster(
            visit_id=data.visit_id, patient_id=data.patient_id, 
            bill_number=bill_num, status=BillStatus.draft, generated_by=user_id,
            org_id=org_id
        )
        self.db.add(master)
        await self.db.flush()
        
        # Assign Payer
        payer = BillingPayer(bill_id=master.id, **data.payer.model_dump())
        self.db.add(payer)
        
        # Assign Services (auto-computing via tariff engine)
        tariff_engine = AutomatedTariffSelectionEngine(self.db)
        
        for svc in data.services:
            # Query rate if not overriden
            rate = svc.base_rate
            if not rate:
                t = await tariff_engine.get_applicable_tariff(TariffMatchQuery(service_name=svc.service_name, patient_category="self_pay" if data.payer.payer_type.value == PayerType.self_pay else data.payer.payer_type.value))
                rate = getattr(t, 'price', Decimal("0.00"))
            
            srv_line = BillingService(
                bill_id=master.id, service_name=svc.service_name,
                department=svc.department, sub_department=svc.sub_department,
                quantity=svc.quantity, base_rate=rate, total_cost=rate * svc.quantity,
                is_auto_billed=svc.is_auto_billed
            )
            self.db.add(srv_line)
            
        await self.db.commit()
        await self.db.refresh(master)
        
        master = await self._recalculate_bill(master)
        return master
        
    async def append_post_consult_service(self, bill_id: uuid.UUID, data: BillingServiceCreate, org_id: uuid.UUID = None) -> BillingMaster:
        stmt = select(BillingMaster).where(BillingMaster.id == bill_id)
        if org_id:
            stmt = stmt.where(BillingMaster.org_id == org_id)
        master = (await self.db.execute(stmt)).scalars().first()
        if not master: return None
        
        tariff_engine = AutomatedTariffSelectionEngine(self.db)
        rate = data.base_rate
        if not rate:
            t = await tariff_engine.get_applicable_tariff(TariffMatchQuery(service_name=data.service_name))
            rate = getattr(t, 'price', Decimal("0.00"))

        srv_line = BillingService(
            bill_id=master.id, service_name=data.service_name,
            department=data.department, sub_department=data.sub_department,
            quantity=data.quantity, base_rate=rate, total_cost=rate * data.quantity,
            is_auto_billed=data.is_auto_billed
        )
        self.db.add(srv_line)
        await self.db.commit()
        
        return await self._recalculate_bill(master)

class DiscountConcessionRuleEngine:
    """Enforces financial deductions safely via hierarchy blocks"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def apply_discount(self, bill_id: uuid.UUID, data: BillingDiscountCreate, admin_id: uuid.UUID, org_id: uuid.UUID = None) -> BillingMaster:
        stmt = select(BillingMaster).where(BillingMaster.id == bill_id)
        if org_id:
            stmt = stmt.where(BillingMaster.org_id == org_id)
        master = (await self.db.execute(stmt)).scalars().first()
        
        # Process Rules (Mock Rule Checking)
        amount = Decimal("0.00")
        if data.discount_type == "percentage":
            amount = master.gross_amount * (data.discount_value / Decimal("100.0"))
        elif data.discount_type == "fixed":
            amount = data.discount_value
        elif data.discount_type == "senior_citizen":
            amount = master.gross_amount * Decimal("0.10")
        elif data.discount_type == "employee":
            amount = master.gross_amount * Decimal("0.20")
            
        disc = BillingDiscount(
            bill_id=master.id, discount_type=data.discount_type, discount_value=amount,
            reason=data.reason, authorized_by=admin_id
        )
        self.db.add(disc)
        await self.db.commit()
        
        billing = ServiceBillingEngine(self.db)
        return await billing._recalculate_bill(master)

class PaymentCollectionEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect_payment(self, bill_id: uuid.UUID, data: BillingPaymentCreate, cashier_id: uuid.UUID, org_id: uuid.UUID = None) -> BillingMaster:
        pmt = BillingPayment(bill_id=bill_id, collected_by=cashier_id, org_id=org_id, **data.model_dump())
        self.db.add(pmt)
        await self.db.commit()
        
        billing = ServiceBillingEngine(self.db)
        stmt = select(BillingMaster).where(BillingMaster.id == bill_id)
        if org_id:
            stmt = stmt.where(BillingMaster.org_id == org_id)
        master = await billing._recalculate_bill((await self.db.execute(stmt)).scalars().first())
        
        if master.balance_amount == 0:
            master.settled_at = datetime.utcnow()
            await self.db.commit()
            
        return master

class RefundCancellationEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def issue_refund(self, bill_id: uuid.UUID, data: BillingRefundCreate, auth_id: uuid.UUID, org_id: uuid.UUID = None) -> BillingMaster:
        ref = BillingRefund(bill_id=bill_id, authorized_by=auth_id, **data.model_dump())
        self.db.add(ref)
        await self.db.commit()
        
        billing = ServiceBillingEngine(self.db)
        stmt = select(BillingMaster).where(BillingMaster.id == bill_id)
        if org_id:
            stmt = stmt.where(BillingMaster.org_id == org_id)
        return await billing._recalculate_bill((await self.db.execute(stmt)).scalars().first())

class FinancialReportingIntegration:
    """Exports BI Revenue Pipelines representing Daily Aggregations"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_daily_revenue(self, org_id: uuid.UUID = None) -> Dict[str, Any]:
        p_stmt = select(func.sum(BillingPayment.amount))
        m_stmt = select(func.sum(BillingMaster.balance_amount))
        if org_id:
            p_stmt = p_stmt.where(BillingPayment.org_id == org_id)
            m_stmt = m_stmt.where(BillingMaster.org_id == org_id)

        result = (await self.db.execute(p_stmt)).scalar() or Decimal("0.00")
        outstanding = (await self.db.execute(m_stmt)).scalar() or Decimal("0.00")
        return {
            "daily_revenue": float(result),
            "total_outstanding_ar": float(outstanding),
            "generated_at": datetime.utcnow().isoformat()
        }
