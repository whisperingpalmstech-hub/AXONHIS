"""
Billing Masters — Database Models
==================================
Complete billing configuration system per FRD:
- Service Group / Service Masters
- Patient Category / Payment Entitlement
- Tariff / Price Masters with variable pricing
- Package Engine (OPD/IPD/Daycare, gender, CAP, all-inclusive, multi-visit)
- Taxation, Currency, Discount Configuration
- Deposit Management
- Credit/Debit Notes
- Bill Estimation
- Auto Charge Posting Rules
- Insurance & Corporate Contract Masters

All models include org_id for multi-tenancy.
"""
import uuid
from datetime import datetime, timezone, date
from enum import StrEnum
from sqlalchemy import (
    Column, String, Text, DateTime, Date, Boolean, Integer, Numeric,
    ForeignKey, JSON, UniqueConstraint, CheckConstraint, Index, Float
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


# ════════════════════════════════════════════════════════════════
#  ENUMS
# ════════════════════════════════════════════════════════════════

class BillType(StrEnum):
    opd = "opd"
    ipd = "ipd"
    er = "er"
    daycare = "daycare"
    pharmacy = "pharmacy"

class BillStage(StrEnum):
    draft = "draft"
    on_hold = "on_hold"           # Partial payment made, reason captured
    settled = "settled"           # Full payment done
    interim = "interim"           # Running IPD bill
    cancellation = "cancellation" # Cancelled bill
    intermediate = "intermediate" # Partial final bill during IPD
    estimated = "estimated"       # Estimation bill
    refunded = "refunded"

class PaymentEntitlementType(StrEnum):
    self_pay = "self_pay"
    insurance = "insurance"
    corporate = "corporate"
    government = "government"

class DiscountLevel(StrEnum):
    bill = "bill"
    service_group = "service_group"
    service = "service"

class DepositType(StrEnum):
    encounter = "encounter"           # Against specific encounter
    service_group = "service_group"   # Against service group/pharmacy
    active = "active"                 # Against forthcoming encounters
    reservation = "reservation"       # Against bed/surgery reservation

class NoteType(StrEnum):
    credit = "credit"
    debit = "debit"

class PackageType(StrEnum):
    opd = "opd"
    ipd = "ipd"
    daycare = "daycare"
    ehc = "ehc"         # Executive Health Check
    cap = "cap"         # CAP package (co-pay)
    all_inclusive = "all_inclusive"
    either_or = "either_or"
    multi_visit = "multi_visit"

class PackageGender(StrEnum):
    male = "male"
    female = "female"
    common = "common"


# ════════════════════════════════════════════════════════════════
#  1. SERVICE GROUP MASTER
# ════════════════════════════════════════════════════════════════

class ServiceGroup(Base):
    """Hierarchical categorization of services (e.g., Consultation, Laboratory, Radiology, Pharmacy, Procedures)."""
    __tablename__ = "billing_service_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parent_group_id = Column(UUID(as_uuid=True), ForeignKey("billing_service_groups.id"), nullable=True)  # For hierarchy
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Integration flags
    is_pharmacy = Column(Boolean, default=False)
    is_lab = Column(Boolean, default=False)
    is_radiology = Column(Boolean, default=False)
    is_procedure = Column(Boolean, default=False)
    is_consultation = Column(Boolean, default=False)
    is_bed_charge = Column(Boolean, default=False)
    is_nursing = Column(Boolean, default=False)
    is_ot = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    services = relationship("ServiceMaster", back_populates="service_group", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("org_id", "code", name="uq_service_group_code"),
        Index("ix_svc_grp_org", "org_id"),
    )


# ════════════════════════════════════════════════════════════════
#  2. SERVICE MASTER
# ════════════════════════════════════════════════════════════════

class ServiceMaster(Base):
    """Individual billable service definitions linked to a service group."""
    __tablename__ = "billing_service_master"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    service_group_id = Column(UUID(as_uuid=True), ForeignKey("billing_service_groups.id"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Pricing attributes
    base_price = Column(Numeric(12, 2), nullable=False, default=0)
    material_price = Column(Numeric(12, 2), nullable=True)  # Separate material component
    is_variable_pricing = Column(Boolean, default=False)  # Uses tariff-based pricing
    is_stat_applicable = Column(Boolean, default=False)   # After-hours surcharge flag
    stat_percentage = Column(Numeric(5, 2), default=0)    # Surcharge percentage

    # Tax
    tax_group_id = Column(UUID(as_uuid=True), ForeignKey("billing_tax_groups.id"), nullable=True)
    is_taxable = Column(Boolean, default=True)

    # Clinical linkage
    department = Column(String(100), nullable=True)
    sub_department = Column(String(100), nullable=True)
    is_auto_post = Column(Boolean, default=False)  # Auto charge posting
    requires_consent = Column(Boolean, default=False)

    # Flags
    is_active = Column(Boolean, default=True)
    is_package_eligible = Column(Boolean, default=True)
    is_discount_eligible = Column(Boolean, default=True)
    is_refundable = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    service_group = relationship("ServiceGroup", back_populates="services")
    tariff_entries = relationship("TariffEntry", back_populates="service", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("org_id", "code", name="uq_service_master_code"),
    )


# ════════════════════════════════════════════════════════════════
#  3. PATIENT CATEGORY MASTER
# ════════════════════════════════════════════════════════════════

class PatientCategory(Base):
    """Patient billing categories (National, Foreign, BPL, Staff, etc.)."""
    __tablename__ = "billing_patient_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)  # e.g., "National", "Foreign National", "BPL", "Staff", "VIP"
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("org_id", "code", name="uq_patient_category_code"),
    )


# ════════════════════════════════════════════════════════════════
#  4. PAYMENT ENTITLEMENT MASTER
# ════════════════════════════════════════════════════════════════

class PaymentEntitlement(Base):
    """Payment responsibility types (Self-Pay, Insurance, Corporate, Government)."""
    __tablename__ = "billing_payment_entitlements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    entitlement_type = Column(String(50), nullable=False)  # self_pay, insurance, corporate, government
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("org_id", "code", name="uq_payment_entitlement_code"),
    )


# ════════════════════════════════════════════════════════════════
#  5. CURRENCY MASTER
# ════════════════════════════════════════════════════════════════

class CurrencyMaster(Base):
    """Multi-currency support with denominations."""
    __tablename__ = "billing_currencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(10), nullable=False)  # INR, USD, AED
    name = Column(String(100), nullable=False)
    symbol = Column(String(10), nullable=False)
    is_default = Column(Boolean, default=False)
    exchange_rate = Column(Numeric(12, 6), default=1.0)  # Rate relative to default currency
    denominations = Column(JSONB, nullable=True)  # e.g., [2000, 500, 200, 100, 50, 20, 10, 5, 2, 1]
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("org_id", "code", name="uq_currency_code"),
    )


# ════════════════════════════════════════════════════════════════
#  6. MODE OF PAYMENT MASTER
# ════════════════════════════════════════════════════════════════

class PaymentModeMaster(Base):
    """Supported payment modes (Cash, Card, UPI, Cheque, E-Transfer, etc.)."""
    __tablename__ = "billing_payment_modes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    requires_reference = Column(Boolean, default=False)  # Card/UPI needs transaction ref
    requires_bank_details = Column(Boolean, default=False)  # Cheque needs bank info
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("org_id", "code", name="uq_payment_mode_code"),
    )


# ════════════════════════════════════════════════════════════════
#  7. TARIFF / PRICE MASTER (Variable Pricing Engine)
# ════════════════════════════════════════════════════════════════

class TariffPlan(Base):
    """Base tariff plans — e.g., Standard, Corporate-A, Insurance-Panel-B."""
    __tablename__ = "billing_tariff_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Derivation
    parent_tariff_id = Column(UUID(as_uuid=True), ForeignKey("billing_tariff_plans.id"), nullable=True)
    derivation_percentage = Column(Numeric(5, 2), nullable=True)  # e.g., parent_price * (1 + derivation_percentage/100)

    # Applicability
    patient_category_id = Column(UUID(as_uuid=True), ForeignKey("billing_patient_categories.id"), nullable=True)
    payment_entitlement_id = Column(UUID(as_uuid=True), ForeignKey("billing_payment_entitlements.id"), nullable=True)
    bed_category = Column(String(100), nullable=True)  # General, Semi-Private, Private, Suite, ICU

    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    entries = relationship("TariffEntry", back_populates="tariff_plan", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("org_id", "code", name="uq_tariff_plan_code"),
    )


class TariffEntry(Base):
    """Individual price entries per service × tariff plan."""
    __tablename__ = "billing_tariff_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    tariff_plan_id = Column(UUID(as_uuid=True), ForeignKey("billing_tariff_plans.id"), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("billing_service_master.id"), nullable=False)

    price = Column(Numeric(12, 2), nullable=False)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    tariff_plan = relationship("TariffPlan", back_populates="entries")
    service = relationship("ServiceMaster", back_populates="tariff_entries")

    __table_args__ = (
        UniqueConstraint("org_id", "tariff_plan_id", "service_id", "valid_from", name="uq_tariff_entry"),
    )


# ════════════════════════════════════════════════════════════════
#  8. TAX CONFIGURATION
# ════════════════════════════════════════════════════════════════

class TaxGroup(Base):
    """Tax groups with GST components."""
    __tablename__ = "billing_tax_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    total_percentage = Column(Numeric(5, 2), nullable=False, default=0)
    is_active = Column(Boolean, default=True)

    # GST components
    cgst_percentage = Column(Numeric(5, 2), default=0)
    sgst_percentage = Column(Numeric(5, 2), default=0)
    igst_percentage = Column(Numeric(5, 2), default=0)
    cess_percentage = Column(Numeric(5, 2), default=0)

    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("org_id", "code", name="uq_tax_group_code"),
    )


# ════════════════════════════════════════════════════════════════
#  9. DISCOUNT CONFIGURATION MASTER
# ════════════════════════════════════════════════════════════════

class DiscountReasonMaster(Base):
    """Predefined discount reasons."""
    __tablename__ = "billing_discount_reasons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("org_id", "code", name="uq_discount_reason_code"),
    )


class DiscountAuthority(Base):
    """Which roles can give how much discount (authority-based)."""
    __tablename__ = "billing_discount_authorities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    role_code = Column(String(100), nullable=False)
    max_percentage = Column(Numeric(5, 2), nullable=True)
    max_absolute_amount = Column(Numeric(12, 2), nullable=True)
    discount_level = Column(String(30), nullable=False, default=DiscountLevel.bill)  # bill, service_group, service
    requires_approval_above = Column(Numeric(12, 2), nullable=True)  # Escalation threshold
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PromotionalDiscount(Base):
    """Time-bound promotional discounts with targeting criteria."""
    __tablename__ = "billing_promotional_discounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Targeting
    applicable_service_ids = Column(JSONB, nullable=True)       # List of service IDs
    applicable_service_group_ids = Column(JSONB, nullable=True) # List of service group IDs
    gender_filter = Column(String(20), nullable=True)           # male, female, all
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)
    diagnosis_codes = Column(JSONB, nullable=True)              # ICD codes

    # Discount
    discount_percentage = Column(Numeric(5, 2), nullable=True)
    discount_amount = Column(Numeric(12, 2), nullable=True)

    # Validity
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ConcessionRule(Base):
    """Concession rules per patient category / payment entitlement."""
    __tablename__ = "billing_concession_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_category_id = Column(UUID(as_uuid=True), ForeignKey("billing_patient_categories.id"), nullable=True)
    payment_entitlement_id = Column(UUID(as_uuid=True), ForeignKey("billing_payment_entitlements.id"), nullable=True)
    service_group_id = Column(UUID(as_uuid=True), ForeignKey("billing_service_groups.id"), nullable=True)
    service_id = Column(UUID(as_uuid=True), ForeignKey("billing_service_master.id"), nullable=True)

    concession_percentage = Column(Numeric(5, 2), nullable=True)
    concession_amount = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ════════════════════════════════════════════════════════════════
#  10. PACKAGE MASTER
# ════════════════════════════════════════════════════════════════

class PackageMaster(Base):
    """Billing packages (OPD/IPD/Daycare/EHC/CAP/All-Inclusive/Multi-Visit)."""
    __tablename__ = "billing_packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    package_type = Column(String(30), nullable=False)  # PackageType enum
    gender = Column(String(20), default="common")      # PackageGender enum

    # Pricing
    package_amount = Column(Numeric(12, 2), nullable=False)
    includes_pharma_estimate = Column(Boolean, default=False)
    pharma_estimated_cost = Column(Numeric(12, 2), default=0)

    # IPD-specific
    bed_category = Column(String(100), nullable=True)
    included_stay_days = Column(Integer, nullable=True)
    icu_days_included = Column(Integer, nullable=True)

    # Multi-visit
    total_visits = Column(Integer, nullable=True)  # For multi-visit packages

    # CAP
    cap_amount_per_service_group = Column(JSONB, nullable=True)  # {"service_group_id": cap_amount}

    # Corporate linkage
    corporate_contract_id = Column(UUID(as_uuid=True), ForeignKey("billing_corporate_contracts.id"), nullable=True)

    # Version control
    version = Column(Integer, default=1)
    previous_version_id = Column(UUID(as_uuid=True), ForeignKey("billing_packages.id"), nullable=True)

    # Validity
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    inclusions = relationship("PackageInclusion", back_populates="package", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("org_id", "code", "version", name="uq_package_code_version"),
    )


class PackageInclusion(Base):
    """Services included/excluded in a package."""
    __tablename__ = "billing_package_inclusions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    package_id = Column(UUID(as_uuid=True), ForeignKey("billing_packages.id"), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("billing_service_master.id"), nullable=True)
    service_group_id = Column(UUID(as_uuid=True), ForeignKey("billing_service_groups.id"), nullable=True)

    inclusion_type = Column(String(30), nullable=False, default="included")  # included, excluded, either_or, forceful_include
    max_quantity = Column(Integer, nullable=True)  # Max allowed quantity within package
    either_or_group = Column(String(50), nullable=True)  # Group ID for either-or options

    package = relationship("PackageMaster", back_populates="inclusions")


# ════════════════════════════════════════════════════════════════
#  11. DEPOSIT MANAGEMENT
# ════════════════════════════════════════════════════════════════

class BillingDeposit(Base):
    """Patient deposits — encounter-specific, service-group, active, or reservation."""
    __tablename__ = "billing_deposits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), nullable=True)  # Null for active/family deposits
    deposit_type = Column(String(30), nullable=False)  # DepositType enum

    # Financial
    deposit_amount = Column(Numeric(12, 2), nullable=False)
    utilized_amount = Column(Numeric(12, 2), default=0)
    refunded_amount = Column(Numeric(12, 2), default=0)
    balance_amount = Column(Numeric(12, 2), nullable=False)

    # Payment details
    payment_mode = Column(String(50), nullable=False)
    transaction_reference = Column(String(255), nullable=True)

    # Target
    service_group_id = Column(UUID(as_uuid=True), ForeignKey("billing_service_groups.id"), nullable=True)
    reservation_id = Column(UUID(as_uuid=True), nullable=True)  # Bed or surgery booking

    # Status
    status = Column(String(30), default="active")  # active, utilized, refunded, expired
    receipt_number = Column(String(50), nullable=True)

    # Family sharing
    is_family_shareable = Column(Boolean, default=False)
    family_member_patient_ids = Column(JSONB, nullable=True)

    collected_by = Column(UUID(as_uuid=True), nullable=False)
    collected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    refunded_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


# ════════════════════════════════════════════════════════════════
#  12. CREDIT / DEBIT NOTES
# ════════════════════════════════════════════════════════════════

class CreditDebitNote(Base):
    """Credit/Debit notes against settled bills."""
    __tablename__ = "billing_credit_debit_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    note_number = Column(String(50), unique=True, nullable=False)
    note_type = Column(String(10), nullable=False)  # credit, debit
    bill_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # References rcm_billing_master.id
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(Text, nullable=False)
    adjustment_type = Column(String(50), nullable=True)  # "add_to_next_bill", "separate_bill"

    # Two-step approval (per FRD)
    status = Column(String(30), default="pending")  # pending, level1_approved, approved, rejected
    requested_by = Column(UUID(as_uuid=True), nullable=False)
    level1_approved_by = Column(UUID(as_uuid=True), nullable=True)
    level1_approved_at = Column(DateTime(timezone=True), nullable=True)
    final_approved_by = Column(UUID(as_uuid=True), nullable=True)
    final_approved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


# ════════════════════════════════════════════════════════════════
#  13. BILL ESTIMATION
# ════════════════════════════════════════════════════════════════

class BillEstimation(Base):
    """Pre-procedure/pre-admission cost estimation."""
    __tablename__ = "billing_estimations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    estimation_number = Column(String(50), unique=True, nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=True)  # Null for unregistered

    # Estimation params
    patient_name = Column(String(255), nullable=True)  # For unregistered
    patient_category_id = Column(UUID(as_uuid=True), ForeignKey("billing_patient_categories.id"), nullable=True)
    payment_entitlement_id = Column(UUID(as_uuid=True), ForeignKey("billing_payment_entitlements.id"), nullable=True)
    bill_type = Column(String(20), nullable=False)  # opd, ipd, daycare, er
    bed_category = Column(String(100), nullable=True)
    expected_stay_days = Column(Integer, nullable=True)
    package_id = Column(UUID(as_uuid=True), ForeignKey("billing_packages.id"), nullable=True)

    # Financial
    estimated_service_amount = Column(Numeric(12, 2), default=0)
    estimated_pharmacy_amount = Column(Numeric(12, 2), default=0)
    estimated_consumable_amount = Column(Numeric(12, 2), default=0)
    estimated_tax_amount = Column(Numeric(12, 2), default=0)
    total_estimated_amount = Column(Numeric(12, 2), nullable=False)

    # Actual comparison (filled after billing)
    actual_bill_id = Column(UUID(as_uuid=True), nullable=True)
    actual_amount = Column(Numeric(12, 2), nullable=True)
    variance_amount = Column(Numeric(12, 2), nullable=True)

    # Breakdown
    estimation_details = Column(JSONB, nullable=True)  # Line-item breakdown

    status = Column(String(30), default="active")  # active, expired, converted
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ════════════════════════════════════════════════════════════════
#  14. INSURANCE & CORPORATE CONTRACT MASTERS
# ════════════════════════════════════════════════════════════════

class BillingInsuranceProvider(Base):
    """Insurance companies and TPAs (billing context)."""
    __tablename__ = "billing_insurance_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    tpa_name = Column(String(255), nullable=True)
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)

    # Financial terms
    tariff_plan_id = Column(UUID(as_uuid=True), ForeignKey("billing_tariff_plans.id"), nullable=True)
    payment_terms_days = Column(Integer, default=30)
    tds_percentage = Column(Numeric(5, 2), default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("org_id", "code", name="uq_insurance_provider_code"),
    )


class CorporateContract(Base):
    """Corporate billing contracts with employers."""
    __tablename__ = "billing_corporate_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    code = Column(String(50), nullable=False)
    company_name = Column(String(255), nullable=False)
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)

    # Financial terms
    tariff_plan_id = Column(UUID(as_uuid=True), ForeignKey("billing_tariff_plans.id"), nullable=True)
    payment_terms_days = Column(Integer, default=30)
    credit_limit = Column(Numeric(14, 2), nullable=True)
    tds_percentage = Column(Numeric(5, 2), default=0)

    # Inclusions/Exclusions
    excluded_service_group_ids = Column(JSONB, nullable=True)
    included_service_group_ids = Column(JSONB, nullable=True)

    # Validity
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("org_id", "code", name="uq_corporate_contract_code"),
    )


class PatientInsuranceDetail(Base):
    """Per-patient insurance details linked to encounters."""
    __tablename__ = "billing_patient_insurance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), nullable=True)

    insurance_provider_id = Column(UUID(as_uuid=True), ForeignKey("billing_insurance_providers.id"), nullable=False)
    policy_number = Column(String(100), nullable=False)
    member_id = Column(String(100), nullable=True)
    group_number = Column(String(100), nullable=True)

    sum_insured = Column(Numeric(14, 2), nullable=True)
    available_balance = Column(Numeric(14, 2), nullable=True)
    co_pay_percentage = Column(Numeric(5, 2), default=0)

    # Authorization
    authorization_number = Column(String(100), nullable=True)
    authorized_amount = Column(Numeric(14, 2), nullable=True)
    authorization_status = Column(String(30), default="pending")  # pending, pre_auth, approved, denied
    authorization_expiry = Column(Date, nullable=True)

    # Per-day eligibility
    eligible_bed_category = Column(String(100), nullable=True)
    per_day_room_limit = Column(Numeric(12, 2), nullable=True)

    # Consumption tracking
    consumed_amount = Column(Numeric(14, 2), default=0)
    sequence_order = Column(Integer, default=1)  # For multiple credit companies

    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    is_primary = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ════════════════════════════════════════════════════════════════
#  15. AUTO CHARGE POSTING RULES
# ════════════════════════════════════════════════════════════════

class AutoChargePostingRule(Base):
    """Rules for auto-posting charges (e.g., daily bed charges, nursing charges)."""
    __tablename__ = "billing_auto_charge_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("billing_service_master.id"), nullable=False)

    # Trigger
    trigger_type = Column(String(50), nullable=False)  # daily, on_admission, on_transfer, on_procedure
    trigger_interval_hours = Column(Integer, nullable=True)  # For recurring charges
    applies_to_bill_type = Column(String(20), nullable=True)  # ipd, er, daycare

    # Pricing
    use_tariff_pricing = Column(Boolean, default=True)
    fixed_price = Column(Numeric(12, 2), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ════════════════════════════════════════════════════════════════
#  16. CHANGE OF PAYEE TRACKING
# ════════════════════════════════════════════════════════════════

class PayeeChangeLog(Base):
    """Tracks mid-stay payee changes (Self ↔ Insurance ↔ Corporate)."""
    __tablename__ = "billing_payee_changes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), nullable=False)
    bill_id = Column(UUID(as_uuid=True), nullable=False)

    old_payer_type = Column(String(50), nullable=False)
    new_payer_type = Column(String(50), nullable=False)
    old_insurance_id = Column(UUID(as_uuid=True), nullable=True)
    new_insurance_id = Column(UUID(as_uuid=True), nullable=True)
    old_corporate_id = Column(UUID(as_uuid=True), nullable=True)
    new_corporate_id = Column(UUID(as_uuid=True), nullable=True)

    reason = Column(Text, nullable=True)
    recalculation_done = Column(Boolean, default=False)

    changed_by = Column(UUID(as_uuid=True), nullable=False)
    changed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
