"""
Billing Masters — Service Layer
==================================
Core business logic for pricing, packaging, taxation, deposits,
credit/debit notes, and estimation. This is the central pricing engine
that ALL other modules (OPD, IPD, ER, Pharmacy, Lab, Store) call into
for financial operations.

Interconnection Points:
- OPD/IPD/ER → PricingEngine.calculate_price() for service charges
- Pharmacy → PricingEngine for medication billing + DepositService for utilization
- Lab/Radiology → PricingEngine for test billing
- IPD → PackageEngine for package billing, DepositService for admission deposits
- All Modules → TaxEngine for GST calculation
"""
import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    ServiceGroup, ServiceMaster, PatientCategory, PaymentEntitlement,
    CurrencyMaster, PaymentModeMaster, TariffPlan, TariffEntry,
    TaxGroup, DiscountReasonMaster, DiscountAuthority, PromotionalDiscount,
    ConcessionRule, PackageMaster, PackageInclusion, BillingDeposit,
    CreditDebitNote, BillEstimation, BillingInsuranceProvider as InsuranceProvider, CorporateContract,
    PatientInsuranceDetail, AutoChargePostingRule, PayeeChangeLog
)
from .schemas import (
    ServiceGroupCreate, ServiceMasterCreate, PatientCategoryCreate,
    PaymentEntitlementCreate, CurrencyCreate, PaymentModeCreate,
    TariffPlanCreate, TariffEntryCreate, TaxGroupCreate,
    DiscountReasonCreate, DiscountAuthorityCreate, PromotionalDiscountCreate,
    PackageCreate, PackageInclusionCreate,
    DepositCreate, DepositUtilizeRequest, DepositRefundRequest,
    CreditDebitNoteCreate, NoteApprovalRequest,
    BillEstimationCreate, InsuranceProviderCreate, CorporateContractCreate,
    PatientInsuranceCreate, PriceCalculationRequest, PriceCalculationResponse
)


def _now():
    return datetime.now(timezone.utc)


def _gen_number(prefix: str) -> str:
    """Generate a unique sequential-style number."""
    ts = _now().strftime("%Y%m%d%H%M%S")
    short = str(uuid.uuid4())[:6].upper()
    return f"{prefix}-{ts}-{short}"


# ════════════════════════════════════════════════════════════════
#  MASTER CRUD SERVICE (Generic for all config tables)
# ════════════════════════════════════════════════════════════════

class BillingMasterCRUD:
    """Generic CRUD for billing master tables — used by all master endpoints."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_service_group(self, data: ServiceGroupCreate, org_id: uuid.UUID) -> ServiceGroup:
        obj = ServiceGroup(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list_service_groups(self, org_id: uuid.UUID, active_only: bool = True) -> List[ServiceGroup]:
        stmt = select(ServiceGroup).where(ServiceGroup.org_id == org_id)
        if active_only:
            stmt = stmt.where(ServiceGroup.is_active == True)
        stmt = stmt.order_by(ServiceGroup.display_order)
        return list((await self.db.execute(stmt)).scalars().all())

    async def create_service(self, data: ServiceMasterCreate, org_id: uuid.UUID) -> ServiceMaster:
        obj = ServiceMaster(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list_services(self, org_id: uuid.UUID, group_id: uuid.UUID = None, active_only: bool = True) -> List[ServiceMaster]:
        stmt = select(ServiceMaster).where(ServiceMaster.org_id == org_id)
        if active_only:
            stmt = stmt.where(ServiceMaster.is_active == True)
        if group_id:
            stmt = stmt.where(ServiceMaster.service_group_id == group_id)
        return list((await self.db.execute(stmt)).scalars().all())

    async def create_patient_category(self, data: PatientCategoryCreate, org_id: uuid.UUID) -> PatientCategory:
        obj = PatientCategory(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list_patient_categories(self, org_id: uuid.UUID) -> List[PatientCategory]:
        stmt = select(PatientCategory).where(PatientCategory.org_id == org_id, PatientCategory.is_active == True)
        return list((await self.db.execute(stmt)).scalars().all())

    async def create_payment_entitlement(self, data: PaymentEntitlementCreate, org_id: uuid.UUID) -> PaymentEntitlement:
        obj = PaymentEntitlement(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list_payment_entitlements(self, org_id: uuid.UUID) -> List[PaymentEntitlement]:
        stmt = select(PaymentEntitlement).where(PaymentEntitlement.org_id == org_id, PaymentEntitlement.is_active == True)
        return list((await self.db.execute(stmt)).scalars().all())

    async def create_currency(self, data: CurrencyCreate, org_id: uuid.UUID) -> CurrencyMaster:
        obj = CurrencyMaster(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list_currencies(self, org_id: uuid.UUID) -> List[CurrencyMaster]:
        stmt = select(CurrencyMaster).where(CurrencyMaster.org_id == org_id, CurrencyMaster.is_active == True)
        return list((await self.db.execute(stmt)).scalars().all())

    async def create_payment_mode(self, data: PaymentModeCreate, org_id: uuid.UUID) -> PaymentModeMaster:
        obj = PaymentModeMaster(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list_payment_modes(self, org_id: uuid.UUID) -> List[PaymentModeMaster]:
        stmt = select(PaymentModeMaster).where(PaymentModeMaster.org_id == org_id, PaymentModeMaster.is_active == True)
        stmt = stmt.order_by(PaymentModeMaster.display_order)
        return list((await self.db.execute(stmt)).scalars().all())

    async def create_tax_group(self, data: TaxGroupCreate, org_id: uuid.UUID) -> TaxGroup:
        obj = TaxGroup(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list_tax_groups(self, org_id: uuid.UUID) -> List[TaxGroup]:
        stmt = select(TaxGroup).where(TaxGroup.org_id == org_id, TaxGroup.is_active == True)
        return list((await self.db.execute(stmt)).scalars().all())

    async def create_tariff_plan(self, data: TariffPlanCreate, org_id: uuid.UUID) -> TariffPlan:
        obj = TariffPlan(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list_tariff_plans(self, org_id: uuid.UUID) -> List[TariffPlan]:
        stmt = select(TariffPlan).where(TariffPlan.org_id == org_id, TariffPlan.is_active == True)
        return list((await self.db.execute(stmt)).scalars().all())

    async def create_tariff_entry(self, data: TariffEntryCreate, org_id: uuid.UUID) -> TariffEntry:
        obj = TariffEntry(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def create_discount_reason(self, data: DiscountReasonCreate, org_id: uuid.UUID) -> DiscountReasonMaster:
        obj = DiscountReasonMaster(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list_discount_reasons(self, org_id: uuid.UUID) -> List[DiscountReasonMaster]:
        stmt = select(DiscountReasonMaster).where(DiscountReasonMaster.org_id == org_id, DiscountReasonMaster.is_active == True)
        return list((await self.db.execute(stmt)).scalars().all())

    async def create_discount_authority(self, data: DiscountAuthorityCreate, org_id: uuid.UUID) -> DiscountAuthority:
        obj = DiscountAuthority(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def create_promotional_discount(self, data: PromotionalDiscountCreate, org_id: uuid.UUID) -> PromotionalDiscount:
        obj = PromotionalDiscount(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def create_insurance_provider(self, data: InsuranceProviderCreate, org_id: uuid.UUID) -> InsuranceProvider:
        obj = InsuranceProvider(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list_insurance_providers(self, org_id: uuid.UUID) -> List[InsuranceProvider]:
        stmt = select(InsuranceProvider).where(InsuranceProvider.org_id == org_id, InsuranceProvider.is_active == True)
        return list((await self.db.execute(stmt)).scalars().all())

    async def create_corporate_contract(self, data: CorporateContractCreate, org_id: uuid.UUID) -> CorporateContract:
        obj = CorporateContract(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list_corporate_contracts(self, org_id: uuid.UUID) -> List[CorporateContract]:
        stmt = select(CorporateContract).where(CorporateContract.org_id == org_id, CorporateContract.is_active == True)
        return list((await self.db.execute(stmt)).scalars().all())

    async def create_patient_insurance(self, data: PatientInsuranceCreate, org_id: uuid.UUID) -> PatientInsuranceDetail:
        obj = PatientInsuranceDetail(**data.model_dump(), org_id=org_id, available_balance=data.sum_insured)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj


# ════════════════════════════════════════════════════════════════
#  PRICING ENGINE (Variable Pricing per FRD)
# ════════════════════════════════════════════════════════════════

class PricingEngine:
    """
    Central pricing engine that ALL modules call to determine the actual price
    of a service. Considers:
    1. Patient category
    2. Payment entitlement (self/insurance/corporate)  
    3. Bed category (for IPD)
    4. Tariff plan applicability
    5. STAT surcharge (after-hours)
    6. Tax calculation (GST)
    7. Active promotions / concessions
    8. Package pricing override
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_price(self, request: PriceCalculationRequest, org_id: uuid.UUID) -> PriceCalculationResponse:
        """Master pricing function called by OPD/IPD/ER/Lab/Pharmacy/Radiology."""
        # 1. Get service details
        service = (await self.db.execute(
            select(ServiceMaster).where(ServiceMaster.id == request.service_id, ServiceMaster.org_id == org_id)
        )).scalars().first()
        if not service:
            raise ValueError(f"Service {request.service_id} not found")

        base_price = service.base_price
        tariff_applied = "base_price"

        # 2. Check for applicable tariff plan (variable pricing)
        if service.is_variable_pricing:
            tariff_price = await self._find_tariff_price(
                service.id, org_id,
                request.patient_category_id,
                request.payment_entitlement_id,
                request.bed_category,
                request.insurance_provider_id,
                request.corporate_contract_id
            )
            if tariff_price is not None:
                base_price, tariff_applied = tariff_price

        # 3. Apply STAT surcharge
        stat_surcharge = Decimal("0")
        if request.is_stat and service.is_stat_applicable:
            stat_surcharge = base_price * service.stat_percentage / Decimal("100")

        # 4. Calculate tax
        tax_amount = Decimal("0")
        tax_breakdown = None
        if service.is_taxable and service.tax_group_id:
            tax_amount, tax_breakdown = await self._calculate_tax(
                service.tax_group_id, base_price + stat_surcharge, org_id
            )

        # 5. Check active promotions
        promo_discount = await self._check_promotions(service.id, org_id)

        # 6. Check concession rules
        concession = await self._check_concessions(
            service.id, org_id,
            request.patient_category_id,
            request.payment_entitlement_id
        )

        total_discount = promo_discount + concession
        net_price = base_price + stat_surcharge + tax_amount - total_discount
        if net_price < 0:
            net_price = Decimal("0")

        return PriceCalculationResponse(
            service_id=service.id,
            service_name=service.name,
            base_price=base_price,
            tariff_applied=tariff_applied,
            stat_surcharge=stat_surcharge,
            tax_amount=tax_amount,
            discount_amount=total_discount,
            net_price=net_price,
            tax_breakdown=tax_breakdown
        )

    async def _find_tariff_price(
        self, service_id, org_id,
        patient_category_id=None, payment_entitlement_id=None,
        bed_category=None, insurance_provider_id=None, corporate_contract_id=None
    ):
        """Find the best matching tariff plan & entry for this context."""
        today = date.today()

        # Look for insurance/corporate-specific tariff first
        tariff_plan_id = None
        if insurance_provider_id:
            ip = (await self.db.execute(
                select(InsuranceProvider).where(InsuranceProvider.id == insurance_provider_id, InsuranceProvider.org_id == org_id)
            )).scalars().first()
            if ip and ip.tariff_plan_id:
                tariff_plan_id = ip.tariff_plan_id

        if not tariff_plan_id and corporate_contract_id:
            cc = (await self.db.execute(
                select(CorporateContract).where(CorporateContract.id == corporate_contract_id, CorporateContract.org_id == org_id)
            )).scalars().first()
            if cc and cc.tariff_plan_id:
                tariff_plan_id = cc.tariff_plan_id

        # If no direct tariff, search by context
        if not tariff_plan_id:
            stmt = select(TariffPlan).where(
                TariffPlan.org_id == org_id,
                TariffPlan.is_active == True
            )
            if patient_category_id:
                stmt = stmt.where(
                    or_(TariffPlan.patient_category_id == patient_category_id, TariffPlan.patient_category_id.is_(None))
                )
            if payment_entitlement_id:
                stmt = stmt.where(
                    or_(TariffPlan.payment_entitlement_id == payment_entitlement_id, TariffPlan.payment_entitlement_id.is_(None))
                )
            if bed_category:
                stmt = stmt.where(
                    or_(TariffPlan.bed_category == bed_category, TariffPlan.bed_category.is_(None))
                )

            plans = list((await self.db.execute(stmt)).scalars().all())
            # Score plans by specificity (more specific = better match)
            best_plan = None
            best_score = -1
            for plan in plans:
                score = 0
                if plan.patient_category_id == patient_category_id and patient_category_id:
                    score += 3
                if plan.payment_entitlement_id == payment_entitlement_id and payment_entitlement_id:
                    score += 2
                if plan.bed_category == bed_category and bed_category:
                    score += 1
                if score > best_score:
                    best_score = score
                    best_plan = plan
            if best_plan:
                tariff_plan_id = best_plan.id

        if not tariff_plan_id:
            return None

        # Get the tariff entry for this service
        entry = (await self.db.execute(
            select(TariffEntry).where(
                TariffEntry.tariff_plan_id == tariff_plan_id,
                TariffEntry.service_id == service_id,
                TariffEntry.is_active == True,
                TariffEntry.org_id == org_id,
                or_(TariffEntry.valid_from.is_(None), TariffEntry.valid_from <= today),
                or_(TariffEntry.valid_to.is_(None), TariffEntry.valid_to >= today),
            ).order_by(TariffEntry.valid_from.desc())
        )).scalars().first()

        if entry:
            plan = (await self.db.execute(
                select(TariffPlan).where(TariffPlan.id == tariff_plan_id)
            )).scalars().first()
            return (entry.price, f"tariff:{plan.code}" if plan else "tariff:matched")

        return None

    async def _calculate_tax(self, tax_group_id, taxable_amount, org_id):
        """Calculate GST breakdown."""
        tg = (await self.db.execute(
            select(TaxGroup).where(TaxGroup.id == tax_group_id, TaxGroup.org_id == org_id, TaxGroup.is_active == True)
        )).scalars().first()
        if not tg:
            return Decimal("0"), None

        today = date.today()
        if tg.valid_from and tg.valid_from > today:
            return Decimal("0"), None
        if tg.valid_to and tg.valid_to < today:
            return Decimal("0"), None

        cgst = taxable_amount * tg.cgst_percentage / Decimal("100")
        sgst = taxable_amount * tg.sgst_percentage / Decimal("100")
        igst = taxable_amount * tg.igst_percentage / Decimal("100")
        cess = taxable_amount * tg.cess_percentage / Decimal("100")
        total = cgst + sgst + igst + cess

        breakdown = {
            "cgst": float(cgst), "sgst": float(sgst),
            "igst": float(igst), "cess": float(cess),
            "total": float(total)
        }
        return total, breakdown

    async def _check_promotions(self, service_id, org_id) -> Decimal:
        """Check for active promotional discounts."""
        today = date.today()
        promos = (await self.db.execute(
            select(PromotionalDiscount).where(
                PromotionalDiscount.org_id == org_id,
                PromotionalDiscount.is_active == True,
                PromotionalDiscount.valid_from <= today,
                PromotionalDiscount.valid_to >= today,
            )
        )).scalars().all()

        for p in promos:
            if p.applicable_service_ids and str(service_id) in [str(x) for x in p.applicable_service_ids]:
                if p.discount_amount:
                    return p.discount_amount
        return Decimal("0")

    async def _check_concessions(self, service_id, org_id, patient_category_id=None, payment_entitlement_id=None) -> Decimal:
        """Check concession rules for this context."""
        if not patient_category_id and not payment_entitlement_id:
            return Decimal("0")

        stmt = select(ConcessionRule).where(
            ConcessionRule.org_id == org_id,
            ConcessionRule.is_active == True,
            or_(ConcessionRule.service_id == service_id, ConcessionRule.service_id.is_(None)),
        )
        if patient_category_id:
            stmt = stmt.where(
                or_(ConcessionRule.patient_category_id == patient_category_id, ConcessionRule.patient_category_id.is_(None))
            )
        if payment_entitlement_id:
            stmt = stmt.where(
                or_(ConcessionRule.payment_entitlement_id == payment_entitlement_id, ConcessionRule.payment_entitlement_id.is_(None))
            )

        rules = (await self.db.execute(stmt)).scalars().all()
        max_concession = Decimal("0")
        for r in rules:
            if r.concession_amount and r.concession_amount > max_concession:
                max_concession = r.concession_amount
        return max_concession


# ════════════════════════════════════════════════════════════════
#  PACKAGE ENGINE
# ════════════════════════════════════════════════════════════════

class PackageEngine:
    """Package billing engine for OPD/IPD/Daycare/EHC/CAP packages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_package(self, data: PackageCreate, org_id: uuid.UUID) -> PackageMaster:
        inclusions_data = data.inclusions
        pkg_data = data.model_dump(exclude={"inclusions"})
        pkg = PackageMaster(**pkg_data, org_id=org_id)
        self.db.add(pkg)
        await self.db.flush()

        for inc_data in inclusions_data:
            inc = PackageInclusion(**inc_data.model_dump(), package_id=pkg.id, org_id=org_id)
            self.db.add(inc)

        await self.db.commit()
        await self.db.refresh(pkg)
        return pkg

    async def list_packages(self, org_id: uuid.UUID, package_type: str = None, active_only: bool = True) -> List[PackageMaster]:
        stmt = select(PackageMaster).where(PackageMaster.org_id == org_id)
        if active_only:
            stmt = stmt.where(PackageMaster.is_active == True)
        if package_type:
            stmt = stmt.where(PackageMaster.package_type == package_type)
        return list((await self.db.execute(stmt)).scalars().all())

    async def check_service_in_package(self, package_id: uuid.UUID, service_id: uuid.UUID, org_id: uuid.UUID) -> bool:
        """Check if a service is included in a package."""
        inc = (await self.db.execute(
            select(PackageInclusion).where(
                PackageInclusion.package_id == package_id,
                PackageInclusion.service_id == service_id,
                PackageInclusion.org_id == org_id,
                PackageInclusion.inclusion_type.in_(["included", "forceful_include"]),
            )
        )).scalars().first()
        return inc is not None


# ════════════════════════════════════════════════════════════════
#  DEPOSIT SERVICE
# ════════════════════════════════════════════════════════════════

class DepositService:
    """Deposit collection, utilization, and refund management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect_deposit(self, data: DepositCreate, collected_by: uuid.UUID, org_id: uuid.UUID) -> BillingDeposit:
        deposit = BillingDeposit(
            **data.model_dump(),
            org_id=org_id,
            balance_amount=data.deposit_amount,
            collected_by=collected_by,
            receipt_number=_gen_number("DEP"),
            status="active"
        )
        self.db.add(deposit)
        await self.db.commit()
        await self.db.refresh(deposit)
        return deposit

    async def utilize_deposit(self, deposit_id: uuid.UUID, request: DepositUtilizeRequest, org_id: uuid.UUID) -> BillingDeposit:
        deposit = (await self.db.execute(
            select(BillingDeposit).where(BillingDeposit.id == deposit_id, BillingDeposit.org_id == org_id)
        )).scalars().first()
        if not deposit:
            raise ValueError("Deposit not found")
        if deposit.balance_amount < request.amount:
            raise ValueError("Insufficient deposit balance")

        deposit.utilized_amount += request.amount
        deposit.balance_amount -= request.amount
        if deposit.balance_amount == 0:
            deposit.status = "utilized"
        await self.db.commit()
        await self.db.refresh(deposit)
        return deposit

    async def refund_deposit(self, deposit_id: uuid.UUID, request: DepositRefundRequest, org_id: uuid.UUID) -> BillingDeposit:
        deposit = (await self.db.execute(
            select(BillingDeposit).where(BillingDeposit.id == deposit_id, BillingDeposit.org_id == org_id)
        )).scalars().first()
        if not deposit:
            raise ValueError("Deposit not found")
        if deposit.balance_amount < request.refund_amount:
            raise ValueError("Refund amount exceeds balance")

        deposit.refunded_amount += request.refund_amount
        deposit.balance_amount -= request.refund_amount
        deposit.refunded_at = _now()
        if deposit.balance_amount == 0:
            deposit.status = "refunded"
        await self.db.commit()
        await self.db.refresh(deposit)
        return deposit

    async def list_patient_deposits(self, patient_id: uuid.UUID, org_id: uuid.UUID) -> List[BillingDeposit]:
        stmt = select(BillingDeposit).where(
            BillingDeposit.patient_id == patient_id,
            BillingDeposit.org_id == org_id
        ).order_by(BillingDeposit.collected_at.desc())
        return list((await self.db.execute(stmt)).scalars().all())


# ════════════════════════════════════════════════════════════════
#  CREDIT / DEBIT NOTE SERVICE
# ════════════════════════════════════════════════════════════════

class CreditDebitNoteService:
    """Two-step approval workflow for credit/debit notes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_note(self, data: CreditDebitNoteCreate, requested_by: uuid.UUID, org_id: uuid.UUID) -> CreditDebitNote:
        prefix = "CN" if data.note_type == "credit" else "DN"
        note = CreditDebitNote(
            **data.model_dump(),
            org_id=org_id,
            note_number=_gen_number(prefix),
            requested_by=requested_by,
            status="pending"
        )
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def approve_note(self, note_id: uuid.UUID, approval: NoteApprovalRequest, approver_id: uuid.UUID, org_id: uuid.UUID) -> CreditDebitNote:
        note = (await self.db.execute(
            select(CreditDebitNote).where(CreditDebitNote.id == note_id, CreditDebitNote.org_id == org_id)
        )).scalars().first()
        if not note:
            raise ValueError("Note not found")

        if approval.action == "reject":
            note.status = "rejected"
        elif note.status == "pending":
            note.status = "level1_approved"
            note.level1_approved_by = approver_id
            note.level1_approved_at = _now()
        elif note.status == "level1_approved":
            note.status = "approved"
            note.final_approved_by = approver_id
            note.final_approved_at = _now()

        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def list_notes(self, org_id: uuid.UUID, status: str = None, patient_id: uuid.UUID = None) -> List[CreditDebitNote]:
        stmt = select(CreditDebitNote).where(CreditDebitNote.org_id == org_id)
        if status:
            stmt = stmt.where(CreditDebitNote.status == status)
        if patient_id:
            stmt = stmt.where(CreditDebitNote.patient_id == patient_id)
        stmt = stmt.order_by(CreditDebitNote.created_at.desc())
        return list((await self.db.execute(stmt)).scalars().all())


# ════════════════════════════════════════════════════════════════
#  BILL ESTIMATION SERVICE
# ════════════════════════════════════════════════════════════════

class BillEstimationService:
    """Pre-admission / pre-procedure cost estimation engine."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pricing = PricingEngine(db)

    async def create_estimation(self, data: BillEstimationCreate, created_by: uuid.UUID, org_id: uuid.UUID) -> BillEstimation:
        # Calculate estimated amounts from service list
        total_service = Decimal("0")
        total_tax = Decimal("0")
        details = []

        for sid in data.service_ids:
            try:
                price_result = await self.pricing.calculate_price(
                    PriceCalculationRequest(
                        service_id=sid,
                        patient_category_id=data.patient_category_id,
                        payment_entitlement_id=data.payment_entitlement_id,
                        bed_category=data.bed_category,
                    ),
                    org_id
                )
                total_service += price_result.base_price
                total_tax += price_result.tax_amount
                details.append({
                    "service_id": str(sid),
                    "service_name": price_result.service_name,
                    "price": float(price_result.net_price),
                })
            except Exception:
                pass

        # Add stay-based charges for IPD
        if data.bill_type == "ipd" and data.expected_stay_days:
            total_service *= data.expected_stay_days  # Simplified; real would itemize

        total = total_service + total_tax
        estimation = BillEstimation(
            org_id=org_id,
            estimation_number=_gen_number("EST"),
            patient_id=data.patient_id,
            patient_name=data.patient_name,
            patient_category_id=data.patient_category_id,
            payment_entitlement_id=data.payment_entitlement_id,
            bill_type=data.bill_type,
            bed_category=data.bed_category,
            expected_stay_days=data.expected_stay_days,
            package_id=data.package_id,
            estimated_service_amount=total_service,
            estimated_tax_amount=total_tax,
            total_estimated_amount=total,
            estimation_details={"services": details},
            created_by=created_by,
            status="active"
        )
        self.db.add(estimation)
        await self.db.commit()
        await self.db.refresh(estimation)
        return estimation


# ════════════════════════════════════════════════════════════════
#  SEEDING SERVICE
# ════════════════════════════════════════════════════════════════

class BillingMasterSeeder:
    """Seeds all default billing master data for a new organization."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = BillingMasterCRUD(db)

    async def seed_all_defaults(self, org_id: uuid.UUID) -> Dict[str, int]:
        """Seed all default billing configuration for a new org. Returns count of seeded entities."""
        counts = {}

        # Patient Categories
        categories = [
            PatientCategoryCreate(code="NATIONAL", name="National", is_default=True, display_order=1),
            PatientCategoryCreate(code="FOREIGN", name="Foreign National", display_order=2),
            PatientCategoryCreate(code="BPL", name="Below Poverty Line", display_order=3),
            PatientCategoryCreate(code="STAFF", name="Hospital Staff", display_order=4),
            PatientCategoryCreate(code="VIP", name="VIP", display_order=5),
        ]
        for c in categories:
            await self.crud.create_patient_category(c, org_id)
        counts["patient_categories"] = len(categories)

        # Payment Entitlements
        entitlements = [
            PaymentEntitlementCreate(code="SELF", entitlement_type="self_pay", name="Self Pay", is_default=True),
            PaymentEntitlementCreate(code="INSURANCE", entitlement_type="insurance", name="Insurance"),
            PaymentEntitlementCreate(code="CORPORATE", entitlement_type="corporate", name="Corporate"),
            PaymentEntitlementCreate(code="GOVT", entitlement_type="government", name="Government Scheme"),
        ]
        for e in entitlements:
            await self.crud.create_payment_entitlement(e, org_id)
        counts["payment_entitlements"] = len(entitlements)

        # Currencies
        currencies = [
            CurrencyCreate(code="INR", name="Indian Rupee", symbol="₹", is_default=True, denominations=[2000, 500, 200, 100, 50, 20, 10, 5, 2, 1]),
            CurrencyCreate(code="USD", name="US Dollar", symbol="$", exchange_rate=Decimal("0.012")),
            CurrencyCreate(code="AED", name="UAE Dirham", symbol="د.إ", exchange_rate=Decimal("0.044")),
        ]
        for c in currencies:
            await self.crud.create_currency(c, org_id)
        counts["currencies"] = len(currencies)

        # Payment Modes
        modes = [
            PaymentModeCreate(code="CASH", name="Cash", display_order=1),
            PaymentModeCreate(code="CARD", name="Credit/Debit Card", requires_reference=True, display_order=2),
            PaymentModeCreate(code="UPI", name="UPI", requires_reference=True, display_order=3),
            PaymentModeCreate(code="CHEQUE", name="Cheque", requires_bank_details=True, display_order=4),
            PaymentModeCreate(code="ETRANSFER", name="E-Transfer / NEFT / RTGS", requires_reference=True, requires_bank_details=True, display_order=5),
            PaymentModeCreate(code="LOYALTY", name="Loyalty Card", requires_reference=True, display_order=6),
            PaymentModeCreate(code="GATEWAY", name="Payment Gateway", requires_reference=True, display_order=7),
        ]
        for m in modes:
            await self.crud.create_payment_mode(m, org_id)
        counts["payment_modes"] = len(modes)

        # Service Groups
        groups = [
            ServiceGroupCreate(code="CONSULT", name="Consultation", is_consultation=True, display_order=1),
            ServiceGroupCreate(code="LAB", name="Laboratory", is_lab=True, display_order=2),
            ServiceGroupCreate(code="RADIOLOGY", name="Radiology & Imaging", is_radiology=True, display_order=3),
            ServiceGroupCreate(code="PHARMACY", name="Pharmacy", is_pharmacy=True, display_order=4),
            ServiceGroupCreate(code="PROCEDURE", name="Procedures", is_procedure=True, display_order=5),
            ServiceGroupCreate(code="BED", name="Bed & Room Charges", is_bed_charge=True, display_order=6),
            ServiceGroupCreate(code="NURSING", name="Nursing Services", is_nursing=True, display_order=7),
            ServiceGroupCreate(code="OT", name="Operation Theatre", is_ot=True, display_order=8),
            ServiceGroupCreate(code="MISC", name="Miscellaneous", display_order=9),
        ]
        for g in groups:
            await self.crud.create_service_group(g, org_id)
        counts["service_groups"] = len(groups)

        # Tax Groups
        tax_groups = [
            TaxGroupCreate(code="GST5", name="GST 5%", total_percentage=Decimal("5"), cgst_percentage=Decimal("2.5"), sgst_percentage=Decimal("2.5")),
            TaxGroupCreate(code="GST12", name="GST 12%", total_percentage=Decimal("12"), cgst_percentage=Decimal("6"), sgst_percentage=Decimal("6")),
            TaxGroupCreate(code="GST18", name="GST 18%", total_percentage=Decimal("18"), cgst_percentage=Decimal("9"), sgst_percentage=Decimal("9")),
            TaxGroupCreate(code="EXEMPT", name="Exempt", total_percentage=Decimal("0")),
        ]
        for t in tax_groups:
            await self.crud.create_tax_group(t, org_id)
        counts["tax_groups"] = len(tax_groups)

        # Discount Reasons
        reasons = [
            DiscountReasonCreate(code="STAFF", name="Staff Discount"),
            DiscountReasonCreate(code="SENIOR", name="Senior Citizen"),
            DiscountReasonCreate(code="BPL", name="Below Poverty Line"),
            DiscountReasonCreate(code="PROMO", name="Promotional Offer"),
            DiscountReasonCreate(code="DOCTOR", name="Doctor Recommendation"),
            DiscountReasonCreate(code="MANAGEMENT", name="Management Approval"),
        ]
        for r in reasons:
            await self.crud.create_discount_reason(r, org_id)
        counts["discount_reasons"] = len(reasons)

        return counts
