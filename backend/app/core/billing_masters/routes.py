"""
Billing Masters — API Routes
==============================
Complete REST API surface for all billing master configuration.
These endpoints are used by ALL clinical modules for pricing,
packaging, taxation, deposits, and financial operations.

Interconnection:
- OPD/IPD/ER frontend → /billing-masters/price-calculate for real-time pricing
- Front Office → /billing-masters/deposits for deposit collection
- Finance → /billing-masters/credit-debit-notes for adjustments
- Admin → /billing-masters/seed for initial setup
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import CurrentUser

from .schemas import (
    ServiceGroupCreate, ServiceGroupOut, ServiceMasterCreate, ServiceMasterOut,
    PatientCategoryCreate, PatientCategoryOut,
    PaymentEntitlementCreate, PaymentEntitlementOut,
    CurrencyCreate, CurrencyOut, PaymentModeCreate, PaymentModeOut,
    TariffPlanCreate, TariffPlanOut, TariffEntryCreate, TariffEntryOut,
    TaxGroupCreate, TaxGroupOut,
    DiscountReasonCreate, DiscountReasonOut, DiscountAuthorityCreate, DiscountAuthorityOut,
    PromotionalDiscountCreate, PromotionalDiscountOut,
    PackageCreate, PackageOut,
    DepositCreate, DepositOut, DepositUtilizeRequest, DepositRefundRequest,
    CreditDebitNoteCreate, CreditDebitNoteOut, NoteApprovalRequest,
    BillEstimationCreate, BillEstimationOut,
    InsuranceProviderCreate, InsuranceProviderOut,
    CorporateContractCreate, CorporateContractOut,
    PatientInsuranceCreate, PatientInsuranceOut,
    PriceCalculationRequest, PriceCalculationResponse,
)
from .services import (
    BillingMasterCRUD, PricingEngine, PackageEngine,
    DepositService, CreditDebitNoteService, BillEstimationService,
    BillingMasterSeeder
)

router = APIRouter(prefix="/billing-masters", tags=["Billing Masters & Configuration"])


# ══════════════════════════════════════════════════════════
#  SERVICE GROUPS
# ══════════════════════════════════════════════════════════

@router.post("/service-groups", response_model=ServiceGroupOut)
async def create_service_group(data: ServiceGroupCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_service_group(data, user.org_id)

@router.get("/service-groups", response_model=List[ServiceGroupOut])
async def list_service_groups(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).list_service_groups(user.org_id)


# ══════════════════════════════════════════════════════════
#  SERVICE MASTER
# ══════════════════════════════════════════════════════════

@router.post("/services", response_model=ServiceMasterOut)
async def create_service(data: ServiceMasterCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_service(data, user.org_id)

@router.get("/services", response_model=List[ServiceMasterOut])
async def list_services(user: CurrentUser, group_id: Optional[uuid.UUID] = None, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).list_services(user.org_id, group_id)


# ══════════════════════════════════════════════════════════
#  PATIENT CATEGORIES
# ══════════════════════════════════════════════════════════

@router.post("/patient-categories", response_model=PatientCategoryOut)
async def create_patient_category(data: PatientCategoryCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_patient_category(data, user.org_id)

@router.get("/patient-categories", response_model=List[PatientCategoryOut])
async def list_patient_categories(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).list_patient_categories(user.org_id)


# ══════════════════════════════════════════════════════════
#  PAYMENT ENTITLEMENTS
# ══════════════════════════════════════════════════════════

@router.post("/payment-entitlements", response_model=PaymentEntitlementOut)
async def create_payment_entitlement(data: PaymentEntitlementCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_payment_entitlement(data, user.org_id)

@router.get("/payment-entitlements", response_model=List[PaymentEntitlementOut])
async def list_payment_entitlements(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).list_payment_entitlements(user.org_id)


# ══════════════════════════════════════════════════════════
#  CURRENCIES
# ══════════════════════════════════════════════════════════

@router.post("/currencies", response_model=CurrencyOut)
async def create_currency(data: CurrencyCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_currency(data, user.org_id)

@router.get("/currencies", response_model=List[CurrencyOut])
async def list_currencies(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).list_currencies(user.org_id)


# ══════════════════════════════════════════════════════════
#  PAYMENT MODES
# ══════════════════════════════════════════════════════════

@router.post("/payment-modes", response_model=PaymentModeOut)
async def create_payment_mode(data: PaymentModeCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_payment_mode(data, user.org_id)

@router.get("/payment-modes", response_model=List[PaymentModeOut])
async def list_payment_modes(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).list_payment_modes(user.org_id)


# ══════════════════════════════════════════════════════════
#  TARIFF PLANS & ENTRIES
# ══════════════════════════════════════════════════════════

@router.post("/tariff-plans", response_model=TariffPlanOut)
async def create_tariff_plan(data: TariffPlanCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_tariff_plan(data, user.org_id)

@router.get("/tariff-plans", response_model=List[TariffPlanOut])
async def list_tariff_plans(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).list_tariff_plans(user.org_id)

@router.post("/tariff-entries", response_model=TariffEntryOut)
async def create_tariff_entry(data: TariffEntryCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_tariff_entry(data, user.org_id)


# ══════════════════════════════════════════════════════════
#  TAX GROUPS
# ══════════════════════════════════════════════════════════

@router.post("/tax-groups", response_model=TaxGroupOut)
async def create_tax_group(data: TaxGroupCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_tax_group(data, user.org_id)

@router.get("/tax-groups", response_model=List[TaxGroupOut])
async def list_tax_groups(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).list_tax_groups(user.org_id)


# ══════════════════════════════════════════════════════════
#  DISCOUNT CONFIGURATION
# ══════════════════════════════════════════════════════════

@router.post("/discount-reasons", response_model=DiscountReasonOut)
async def create_discount_reason(data: DiscountReasonCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_discount_reason(data, user.org_id)

@router.get("/discount-reasons", response_model=List[DiscountReasonOut])
async def list_discount_reasons(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).list_discount_reasons(user.org_id)

@router.post("/discount-authorities", response_model=DiscountAuthorityOut)
async def create_discount_authority(data: DiscountAuthorityCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_discount_authority(data, user.org_id)

@router.post("/promotional-discounts", response_model=PromotionalDiscountOut)
async def create_promotional_discount(data: PromotionalDiscountCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_promotional_discount(data, user.org_id)


# ══════════════════════════════════════════════════════════
#  INSURANCE PROVIDERS
# ══════════════════════════════════════════════════════════

@router.post("/insurance-providers", response_model=InsuranceProviderOut)
async def create_insurance_provider(data: InsuranceProviderCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_insurance_provider(data, user.org_id)

@router.get("/insurance-providers", response_model=List[InsuranceProviderOut])
async def list_insurance_providers(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).list_insurance_providers(user.org_id)


# ══════════════════════════════════════════════════════════
#  CORPORATE CONTRACTS
# ══════════════════════════════════════════════════════════

@router.post("/corporate-contracts", response_model=CorporateContractOut)
async def create_corporate_contract(data: CorporateContractCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_corporate_contract(data, user.org_id)

@router.get("/corporate-contracts", response_model=List[CorporateContractOut])
async def list_corporate_contracts(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).list_corporate_contracts(user.org_id)


# ══════════════════════════════════════════════════════════
#  PATIENT INSURANCE
# ══════════════════════════════════════════════════════════

@router.post("/patient-insurance", response_model=PatientInsuranceOut)
async def create_patient_insurance(data: PatientInsuranceCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillingMasterCRUD(db).create_patient_insurance(data, user.org_id)


# ══════════════════════════════════════════════════════════
#  PACKAGES
# ══════════════════════════════════════════════════════════

@router.post("/packages", response_model=PackageOut)
async def create_package(data: PackageCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await PackageEngine(db).create_package(data, user.org_id)

@router.get("/packages", response_model=List[PackageOut])
async def list_packages(user: CurrentUser, package_type: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    return await PackageEngine(db).list_packages(user.org_id, package_type)


# ══════════════════════════════════════════════════════════
#  VARIABLE PRICING ENGINE (Used by all clinical modules)
# ══════════════════════════════════════════════════════════

@router.post("/price-calculate", response_model=PriceCalculationResponse)
async def calculate_service_price(data: PriceCalculationRequest, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    """Central pricing endpoint used by OPD/IPD/ER/Lab/Pharmacy for real-time price calculation."""
    engine = PricingEngine(db)
    return await engine.calculate_price(data, user.org_id)


# ══════════════════════════════════════════════════════════
#  DEPOSITS
# ══════════════════════════════════════════════════════════

@router.post("/deposits", response_model=DepositOut)
async def collect_deposit(data: DepositCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await DepositService(db).collect_deposit(data, user.id, user.org_id)

@router.get("/deposits/{patient_id}", response_model=List[DepositOut])
async def list_patient_deposits(patient_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await DepositService(db).list_patient_deposits(patient_id, user.org_id)

@router.post("/deposits/{deposit_id}/utilize", response_model=DepositOut)
async def utilize_deposit(deposit_id: uuid.UUID, data: DepositUtilizeRequest, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await DepositService(db).utilize_deposit(deposit_id, data, user.org_id)

@router.post("/deposits/{deposit_id}/refund", response_model=DepositOut)
async def refund_deposit(deposit_id: uuid.UUID, data: DepositRefundRequest, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await DepositService(db).refund_deposit(deposit_id, data, user.org_id)


# ══════════════════════════════════════════════════════════
#  CREDIT / DEBIT NOTES
# ══════════════════════════════════════════════════════════

@router.post("/credit-debit-notes", response_model=CreditDebitNoteOut)
async def create_credit_debit_note(data: CreditDebitNoteCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await CreditDebitNoteService(db).create_note(data, user.id, user.org_id)

@router.post("/credit-debit-notes/{note_id}/approve", response_model=CreditDebitNoteOut)
async def approve_credit_debit_note(note_id: uuid.UUID, data: NoteApprovalRequest, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await CreditDebitNoteService(db).approve_note(note_id, data, user.id, user.org_id)

@router.get("/credit-debit-notes", response_model=List[CreditDebitNoteOut])
async def list_credit_debit_notes(user: CurrentUser, status: Optional[str] = None, patient_id: Optional[uuid.UUID] = None, db: AsyncSession = Depends(get_db)):
    return await CreditDebitNoteService(db).list_notes(user.org_id, status, patient_id)


# ══════════════════════════════════════════════════════════
#  BILL ESTIMATION
# ══════════════════════════════════════════════════════════

@router.post("/estimations", response_model=BillEstimationOut)
async def create_bill_estimation(data: BillEstimationCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await BillEstimationService(db).create_estimation(data, user.id, user.org_id)


# ══════════════════════════════════════════════════════════
#  SEED DEFAULTS (One-time setup for new organization)
# ══════════════════════════════════════════════════════════

@router.post("/seed")
async def seed_billing_masters(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    """Seed all default billing master data for the current organization.
    This populates: Patient Categories, Payment Entitlements, Currencies,
    Payment Modes, Service Groups, Tax Groups, and Discount Reasons."""
    seeder = BillingMasterSeeder(db)
    counts = await seeder.seed_all_defaults(user.org_id)
    return {"status": "ok", "message": "Billing masters seeded successfully", "counts": counts}
