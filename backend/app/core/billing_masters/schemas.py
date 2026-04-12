"""
Billing Masters — Pydantic Schemas
====================================
Request/Response schemas for all billing master configuration APIs.
Interconnected with OPD, IPD, ER, Pharmacy, Lab, Store modules.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal


# ════════════════════════════════════════════════════════════════
#  SERVICE GROUP
# ════════════════════════════════════════════════════════════════

class ServiceGroupCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    parent_group_id: Optional[UUID] = None
    display_order: int = 0
    is_pharmacy: bool = False
    is_lab: bool = False
    is_radiology: bool = False
    is_procedure: bool = False
    is_consultation: bool = False
    is_bed_charge: bool = False
    is_nursing: bool = False
    is_ot: bool = False

class ServiceGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

class ServiceGroupOut(ServiceGroupCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    created_at: datetime
    class Config: from_attributes = True


# ════════════════════════════════════════════════════════════════
#  SERVICE MASTER
# ════════════════════════════════════════════════════════════════

class ServiceMasterCreate(BaseModel):
    service_group_id: UUID
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    base_price: Decimal = Decimal("0")
    material_price: Optional[Decimal] = None
    is_variable_pricing: bool = False
    is_stat_applicable: bool = False
    stat_percentage: Decimal = Decimal("0")
    tax_group_id: Optional[UUID] = None
    is_taxable: bool = True
    department: Optional[str] = None
    sub_department: Optional[str] = None
    is_auto_post: bool = False
    requires_consent: bool = False
    is_package_eligible: bool = True
    is_discount_eligible: bool = True
    is_refundable: bool = True

class ServiceMasterUpdate(BaseModel):
    name: Optional[str] = None
    base_price: Optional[Decimal] = None
    is_active: Optional[bool] = None
    is_stat_applicable: Optional[bool] = None
    stat_percentage: Optional[Decimal] = None

class ServiceMasterOut(ServiceMasterCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    created_at: datetime
    class Config: from_attributes = True


# ════════════════════════════════════════════════════════════════
#  PATIENT CATEGORY
# ════════════════════════════════════════════════════════════════

class PatientCategoryCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    is_default: bool = False
    display_order: int = 0

class PatientCategoryOut(PatientCategoryCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    created_at: datetime
    class Config: from_attributes = True


# ════════════════════════════════════════════════════════════════
#  PAYMENT ENTITLEMENT
# ════════════════════════════════════════════════════════════════

class PaymentEntitlementCreate(BaseModel):
    code: str
    entitlement_type: str  # self_pay, insurance, corporate, government
    name: str
    description: Optional[str] = None
    is_default: bool = False

class PaymentEntitlementOut(PaymentEntitlementCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    created_at: datetime
    class Config: from_attributes = True


# ════════════════════════════════════════════════════════════════
#  CURRENCY, PAYMENT MODE
# ════════════════════════════════════════════════════════════════

class CurrencyCreate(BaseModel):
    code: str
    name: str
    symbol: str
    is_default: bool = False
    exchange_rate: Decimal = Decimal("1.0")
    denominations: Optional[list] = None

class CurrencyOut(CurrencyCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    class Config: from_attributes = True

class PaymentModeCreate(BaseModel):
    code: str
    name: str
    requires_reference: bool = False
    requires_bank_details: bool = False
    display_order: int = 0

class PaymentModeOut(PaymentModeCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    class Config: from_attributes = True


# ════════════════════════════════════════════════════════════════
#  TARIFF PLAN & ENTRIES
# ════════════════════════════════════════════════════════════════

class TariffPlanCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    parent_tariff_id: Optional[UUID] = None
    derivation_percentage: Optional[Decimal] = None
    patient_category_id: Optional[UUID] = None
    payment_entitlement_id: Optional[UUID] = None
    bed_category: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_default: bool = False

class TariffPlanOut(TariffPlanCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    created_at: datetime
    class Config: from_attributes = True

class TariffEntryCreate(BaseModel):
    tariff_plan_id: UUID
    service_id: UUID
    price: Decimal
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

class TariffEntryOut(TariffEntryCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    class Config: from_attributes = True


# ════════════════════════════════════════════════════════════════
#  TAX GROUP
# ════════════════════════════════════════════════════════════════

class TaxGroupCreate(BaseModel):
    code: str
    name: str
    total_percentage: Decimal = Decimal("0")
    cgst_percentage: Decimal = Decimal("0")
    sgst_percentage: Decimal = Decimal("0")
    igst_percentage: Decimal = Decimal("0")
    cess_percentage: Decimal = Decimal("0")
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

class TaxGroupOut(TaxGroupCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    class Config: from_attributes = True


# ════════════════════════════════════════════════════════════════
#  DISCOUNT CONFIGURATION
# ════════════════════════════════════════════════════════════════

class DiscountReasonCreate(BaseModel):
    code: str
    name: str

class DiscountReasonOut(DiscountReasonCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    class Config: from_attributes = True

class DiscountAuthorityCreate(BaseModel):
    role_code: str
    max_percentage: Optional[Decimal] = None
    max_absolute_amount: Optional[Decimal] = None
    discount_level: str = "bill"  # bill, service_group, service
    requires_approval_above: Optional[Decimal] = None

class DiscountAuthorityOut(DiscountAuthorityCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    class Config: from_attributes = True

class PromotionalDiscountCreate(BaseModel):
    name: str
    description: Optional[str] = None
    applicable_service_ids: Optional[list] = None
    applicable_service_group_ids: Optional[list] = None
    gender_filter: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    diagnosis_codes: Optional[list] = None
    discount_percentage: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    valid_from: date
    valid_to: date

class PromotionalDiscountOut(PromotionalDiscountCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    class Config: from_attributes = True


# ════════════════════════════════════════════════════════════════
#  PACKAGE
# ════════════════════════════════════════════════════════════════

class PackageInclusionCreate(BaseModel):
    service_id: Optional[UUID] = None
    service_group_id: Optional[UUID] = None
    inclusion_type: str = "included"
    max_quantity: Optional[int] = None
    either_or_group: Optional[str] = None

class PackageCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    package_type: str  # opd, ipd, daycare, ehc, cap, all_inclusive, either_or, multi_visit
    gender: str = "common"
    package_amount: Decimal
    includes_pharma_estimate: bool = False
    pharma_estimated_cost: Decimal = Decimal("0")
    bed_category: Optional[str] = None
    included_stay_days: Optional[int] = None
    icu_days_included: Optional[int] = None
    total_visits: Optional[int] = None
    cap_amount_per_service_group: Optional[dict] = None
    corporate_contract_id: Optional[UUID] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    inclusions: List[PackageInclusionCreate] = []

class PackageOut(BaseModel):
    id: UUID
    org_id: UUID
    code: str
    name: str
    package_type: str
    gender: str
    package_amount: Decimal
    bed_category: Optional[str]
    included_stay_days: Optional[int]
    total_visits: Optional[int]
    version: int
    is_active: bool
    created_at: datetime
    class Config: from_attributes = True


# ════════════════════════════════════════════════════════════════
#  DEPOSIT
# ════════════════════════════════════════════════════════════════

class DepositCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    deposit_type: str  # encounter, service_group, active, reservation
    deposit_amount: Decimal
    payment_mode: str
    transaction_reference: Optional[str] = None
    service_group_id: Optional[UUID] = None
    reservation_id: Optional[UUID] = None
    is_family_shareable: bool = False
    family_member_patient_ids: Optional[list] = None

class DepositOut(BaseModel):
    id: UUID
    org_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID]
    deposit_type: str
    deposit_amount: Decimal
    utilized_amount: Decimal
    refunded_amount: Decimal
    balance_amount: Decimal
    payment_mode: str
    status: str
    receipt_number: Optional[str]
    collected_at: datetime
    class Config: from_attributes = True

class DepositUtilizeRequest(BaseModel):
    bill_id: UUID
    amount: Decimal

class DepositRefundRequest(BaseModel):
    refund_amount: Decimal
    refund_mode: str
    reason: Optional[str] = None


# ════════════════════════════════════════════════════════════════
#  CREDIT/DEBIT NOTE
# ════════════════════════════════════════════════════════════════

class CreditDebitNoteCreate(BaseModel):
    note_type: str  # credit, debit
    bill_id: UUID
    patient_id: UUID
    amount: Decimal
    reason: str
    adjustment_type: Optional[str] = None  # add_to_next_bill, separate_bill

class CreditDebitNoteOut(CreditDebitNoteCreate):
    id: UUID
    org_id: UUID
    note_number: str
    status: str
    requested_by: UUID
    created_at: datetime
    class Config: from_attributes = True

class NoteApprovalRequest(BaseModel):
    action: str  # approve, reject
    remarks: Optional[str] = None


# ════════════════════════════════════════════════════════════════
#  BILL ESTIMATION
# ════════════════════════════════════════════════════════════════

class BillEstimationCreate(BaseModel):
    patient_id: Optional[UUID] = None
    patient_name: Optional[str] = None
    patient_category_id: Optional[UUID] = None
    payment_entitlement_id: Optional[UUID] = None
    bill_type: str  # opd, ipd, daycare, er
    bed_category: Optional[str] = None
    expected_stay_days: Optional[int] = None
    package_id: Optional[UUID] = None
    service_ids: List[UUID] = []

class BillEstimationOut(BaseModel):
    id: UUID
    org_id: UUID
    estimation_number: str
    patient_id: Optional[UUID]
    bill_type: str
    estimated_service_amount: Decimal
    estimated_pharmacy_amount: Decimal
    estimated_tax_amount: Decimal
    total_estimated_amount: Decimal
    estimation_details: Optional[dict]
    status: str
    created_at: datetime
    class Config: from_attributes = True


# ════════════════════════════════════════════════════════════════
#  INSURANCE & CORPORATE
# ════════════════════════════════════════════════════════════════

class InsuranceProviderCreate(BaseModel):
    code: str
    name: str
    tpa_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tariff_plan_id: Optional[UUID] = None
    payment_terms_days: int = 30
    tds_percentage: Decimal = Decimal("0")

class InsuranceProviderOut(InsuranceProviderCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    class Config: from_attributes = True

class CorporateContractCreate(BaseModel):
    code: str
    company_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tariff_plan_id: Optional[UUID] = None
    payment_terms_days: int = 30
    credit_limit: Optional[Decimal] = None
    tds_percentage: Decimal = Decimal("0")
    excluded_service_group_ids: Optional[list] = None
    included_service_group_ids: Optional[list] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

class CorporateContractOut(CorporateContractCreate):
    id: UUID
    org_id: UUID
    is_active: bool
    class Config: from_attributes = True

class PatientInsuranceCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    insurance_provider_id: UUID
    policy_number: str
    member_id: Optional[str] = None
    group_number: Optional[str] = None
    sum_insured: Optional[Decimal] = None
    co_pay_percentage: Decimal = Decimal("0")
    authorization_number: Optional[str] = None
    authorized_amount: Optional[Decimal] = None
    eligible_bed_category: Optional[str] = None
    per_day_room_limit: Optional[Decimal] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_primary: bool = True

class PatientInsuranceOut(PatientInsuranceCreate):
    id: UUID
    org_id: UUID
    authorization_status: str
    consumed_amount: Decimal
    available_balance: Optional[Decimal]
    is_active: bool
    class Config: from_attributes = True


# ════════════════════════════════════════════════════════════════
#  VARIABLE PRICING QUERY
# ════════════════════════════════════════════════════════════════

class PriceCalculationRequest(BaseModel):
    """Request to calculate the actual price of a service based on all variables."""
    service_id: UUID
    patient_category_id: Optional[UUID] = None
    payment_entitlement_id: Optional[UUID] = None
    bed_category: Optional[str] = None
    is_stat: bool = False
    package_id: Optional[UUID] = None
    insurance_provider_id: Optional[UUID] = None
    corporate_contract_id: Optional[UUID] = None

class PriceCalculationResponse(BaseModel):
    service_id: UUID
    service_name: str
    base_price: Decimal
    tariff_applied: Optional[str] = None
    stat_surcharge: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    net_price: Decimal = Decimal("0")
    tax_breakdown: Optional[dict] = None
