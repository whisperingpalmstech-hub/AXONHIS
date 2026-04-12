-- Sprint 1: Billing Masters & Configuration Engine
-- FRD Reference: BILLING_APPLICATION_FUNCTIONALITY.docx (Gaps 5-15)
-- Creates 19 tables for complete billing configuration

-- 1. Service Groups
CREATE TABLE IF NOT EXISTS billing_service_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_group_id UUID REFERENCES billing_service_groups(id),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_pharmacy BOOLEAN DEFAULT FALSE,
    is_lab BOOLEAN DEFAULT FALSE,
    is_radiology BOOLEAN DEFAULT FALSE,
    is_procedure BOOLEAN DEFAULT FALSE,
    is_consultation BOOLEAN DEFAULT FALSE,
    is_bed_charge BOOLEAN DEFAULT FALSE,
    is_nursing BOOLEAN DEFAULT FALSE,
    is_ot BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    UNIQUE(org_id, code)
);
CREATE INDEX IF NOT EXISTS ix_svc_grp_org ON billing_service_groups(org_id);

-- 2. Tax Groups (needed before Service Master due to FK)
CREATE TABLE IF NOT EXISTS billing_tax_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    total_percentage NUMERIC(5,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    cgst_percentage NUMERIC(5,2) DEFAULT 0,
    sgst_percentage NUMERIC(5,2) DEFAULT 0,
    igst_percentage NUMERIC(5,2) DEFAULT 0,
    cess_percentage NUMERIC(5,2) DEFAULT 0,
    valid_from DATE,
    valid_to DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, code)
);

-- 3. Service Master
CREATE TABLE IF NOT EXISTS billing_service_master (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    service_group_id UUID NOT NULL REFERENCES billing_service_groups(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_price NUMERIC(12,2) DEFAULT 0,
    material_price NUMERIC(12,2),
    is_variable_pricing BOOLEAN DEFAULT FALSE,
    is_stat_applicable BOOLEAN DEFAULT FALSE,
    stat_percentage NUMERIC(5,2) DEFAULT 0,
    tax_group_id UUID REFERENCES billing_tax_groups(id),
    is_taxable BOOLEAN DEFAULT TRUE,
    department VARCHAR(100),
    sub_department VARCHAR(100),
    is_auto_post BOOLEAN DEFAULT FALSE,
    requires_consent BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_package_eligible BOOLEAN DEFAULT TRUE,
    is_discount_eligible BOOLEAN DEFAULT TRUE,
    is_refundable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    UNIQUE(org_id, code)
);
CREATE INDEX IF NOT EXISTS ix_svc_master_org ON billing_service_master(org_id);

-- 4. Patient Categories
CREATE TABLE IF NOT EXISTS billing_patient_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, code)
);

-- 5. Payment Entitlements
CREATE TABLE IF NOT EXISTS billing_payment_entitlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    entitlement_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, code)
);

-- 6. Currencies
CREATE TABLE IF NOT EXISTS billing_currencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    exchange_rate NUMERIC(12,6) DEFAULT 1.0,
    denominations JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, code)
);

-- 7. Payment Modes
CREATE TABLE IF NOT EXISTS billing_payment_modes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    requires_reference BOOLEAN DEFAULT FALSE,
    requires_bank_details BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, code)
);

-- 8. Corporate Contracts (needed before Packages due to FK)
CREATE TABLE IF NOT EXISTS billing_corporate_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    tariff_plan_id UUID,
    payment_terms_days INTEGER DEFAULT 30,
    credit_limit NUMERIC(14,2),
    tds_percentage NUMERIC(5,2) DEFAULT 0,
    excluded_service_group_ids JSONB,
    included_service_group_ids JSONB,
    valid_from DATE,
    valid_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    UNIQUE(org_id, code)
);

-- 9. Tariff Plans
CREATE TABLE IF NOT EXISTS billing_tariff_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_tariff_id UUID REFERENCES billing_tariff_plans(id),
    derivation_percentage NUMERIC(5,2),
    patient_category_id UUID REFERENCES billing_patient_categories(id),
    payment_entitlement_id UUID REFERENCES billing_payment_entitlements(id),
    bed_category VARCHAR(100),
    valid_from DATE,
    valid_to DATE,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    UNIQUE(org_id, code)
);
-- Add FK to corporate_contracts now
ALTER TABLE billing_corporate_contracts ADD CONSTRAINT fk_corp_tariff
    FOREIGN KEY (tariff_plan_id) REFERENCES billing_tariff_plans(id);

-- 10. Tariff Entries
CREATE TABLE IF NOT EXISTS billing_tariff_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    tariff_plan_id UUID NOT NULL REFERENCES billing_tariff_plans(id),
    service_id UUID NOT NULL REFERENCES billing_service_master(id),
    price NUMERIC(12,2) NOT NULL,
    valid_from DATE,
    valid_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, tariff_plan_id, service_id, valid_from)
);

-- 11. Discount Reasons
CREATE TABLE IF NOT EXISTS billing_discount_reasons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(org_id, code)
);

-- 12. Discount Authorities
CREATE TABLE IF NOT EXISTS billing_discount_authorities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    role_code VARCHAR(100) NOT NULL,
    max_percentage NUMERIC(5,2),
    max_absolute_amount NUMERIC(12,2),
    discount_level VARCHAR(30) DEFAULT 'bill',
    requires_approval_above NUMERIC(12,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 13. Promotional Discounts
CREATE TABLE IF NOT EXISTS billing_promotional_discounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    applicable_service_ids JSONB,
    applicable_service_group_ids JSONB,
    gender_filter VARCHAR(20),
    min_age INTEGER,
    max_age INTEGER,
    diagnosis_codes JSONB,
    discount_percentage NUMERIC(5,2),
    discount_amount NUMERIC(12,2),
    valid_from DATE NOT NULL,
    valid_to DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 14. Concession Rules
CREATE TABLE IF NOT EXISTS billing_concession_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    patient_category_id UUID REFERENCES billing_patient_categories(id),
    payment_entitlement_id UUID REFERENCES billing_payment_entitlements(id),
    service_group_id UUID REFERENCES billing_service_groups(id),
    service_id UUID REFERENCES billing_service_master(id),
    concession_percentage NUMERIC(5,2),
    concession_amount NUMERIC(12,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 15. Packages
CREATE TABLE IF NOT EXISTS billing_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    package_type VARCHAR(30) NOT NULL,
    gender VARCHAR(20) DEFAULT 'common',
    package_amount NUMERIC(12,2) NOT NULL,
    includes_pharma_estimate BOOLEAN DEFAULT FALSE,
    pharma_estimated_cost NUMERIC(12,2) DEFAULT 0,
    bed_category VARCHAR(100),
    included_stay_days INTEGER,
    icu_days_included INTEGER,
    total_visits INTEGER,
    cap_amount_per_service_group JSONB,
    corporate_contract_id UUID REFERENCES billing_corporate_contracts(id),
    version INTEGER DEFAULT 1,
    previous_version_id UUID REFERENCES billing_packages(id),
    valid_from DATE,
    valid_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    UNIQUE(org_id, code, version)
);

-- 16. Package Inclusions
CREATE TABLE IF NOT EXISTS billing_package_inclusions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    package_id UUID NOT NULL REFERENCES billing_packages(id),
    service_id UUID REFERENCES billing_service_master(id),
    service_group_id UUID REFERENCES billing_service_groups(id),
    inclusion_type VARCHAR(30) DEFAULT 'included',
    max_quantity INTEGER,
    either_or_group VARCHAR(50)
);

-- 17. Deposits
CREATE TABLE IF NOT EXISTS billing_deposits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    patient_id UUID NOT NULL,
    encounter_id UUID,
    deposit_type VARCHAR(30) NOT NULL,
    deposit_amount NUMERIC(12,2) NOT NULL,
    utilized_amount NUMERIC(12,2) DEFAULT 0,
    refunded_amount NUMERIC(12,2) DEFAULT 0,
    balance_amount NUMERIC(12,2) NOT NULL,
    payment_mode VARCHAR(50) NOT NULL,
    transaction_reference VARCHAR(255),
    service_group_id UUID REFERENCES billing_service_groups(id),
    reservation_id UUID,
    status VARCHAR(30) DEFAULT 'active',
    receipt_number VARCHAR(50),
    is_family_shareable BOOLEAN DEFAULT FALSE,
    family_member_patient_ids JSONB,
    collected_by UUID NOT NULL,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    refunded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_deposits_patient ON billing_deposits(patient_id);
CREATE INDEX IF NOT EXISTS ix_deposits_org ON billing_deposits(org_id);

-- 18. Credit/Debit Notes
CREATE TABLE IF NOT EXISTS billing_credit_debit_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    note_number VARCHAR(50) UNIQUE NOT NULL,
    note_type VARCHAR(10) NOT NULL,
    bill_id UUID NOT NULL,
    patient_id UUID NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    reason TEXT NOT NULL,
    adjustment_type VARCHAR(50),
    status VARCHAR(30) DEFAULT 'pending',
    requested_by UUID NOT NULL,
    level1_approved_by UUID,
    level1_approved_at TIMESTAMPTZ,
    final_approved_by UUID,
    final_approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_cdn_patient ON billing_credit_debit_notes(patient_id);

-- 19. Bill Estimations
CREATE TABLE IF NOT EXISTS billing_estimations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    estimation_number VARCHAR(50) UNIQUE NOT NULL,
    patient_id UUID,
    patient_name VARCHAR(255),
    patient_category_id UUID REFERENCES billing_patient_categories(id),
    payment_entitlement_id UUID REFERENCES billing_payment_entitlements(id),
    bill_type VARCHAR(20) NOT NULL,
    bed_category VARCHAR(100),
    expected_stay_days INTEGER,
    package_id UUID REFERENCES billing_packages(id),
    estimated_service_amount NUMERIC(12,2) DEFAULT 0,
    estimated_pharmacy_amount NUMERIC(12,2) DEFAULT 0,
    estimated_consumable_amount NUMERIC(12,2) DEFAULT 0,
    estimated_tax_amount NUMERIC(12,2) DEFAULT 0,
    total_estimated_amount NUMERIC(12,2) NOT NULL,
    actual_bill_id UUID,
    actual_amount NUMERIC(12,2),
    variance_amount NUMERIC(12,2),
    estimation_details JSONB,
    status VARCHAR(30) DEFAULT 'active',
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 20. Insurance Providers
CREATE TABLE IF NOT EXISTS billing_insurance_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    tpa_name VARCHAR(255),
    contact_person VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    tariff_plan_id UUID REFERENCES billing_tariff_plans(id),
    payment_terms_days INTEGER DEFAULT 30,
    tds_percentage NUMERIC(5,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, code)
);

-- 21. Patient Insurance Details
CREATE TABLE IF NOT EXISTS billing_patient_insurance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    patient_id UUID NOT NULL,
    encounter_id UUID,
    insurance_provider_id UUID NOT NULL REFERENCES billing_insurance_providers(id),
    policy_number VARCHAR(100) NOT NULL,
    member_id VARCHAR(100),
    group_number VARCHAR(100),
    sum_insured NUMERIC(14,2),
    available_balance NUMERIC(14,2),
    co_pay_percentage NUMERIC(5,2) DEFAULT 0,
    authorization_number VARCHAR(100),
    authorized_amount NUMERIC(14,2),
    authorization_status VARCHAR(30) DEFAULT 'pending',
    authorization_expiry DATE,
    eligible_bed_category VARCHAR(100),
    per_day_room_limit NUMERIC(12,2),
    consumed_amount NUMERIC(14,2) DEFAULT 0,
    sequence_order INTEGER DEFAULT 1,
    valid_from DATE,
    valid_to DATE,
    is_primary BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_pat_ins_patient ON billing_patient_insurance(patient_id);

-- 22. Auto Charge Posting Rules
CREATE TABLE IF NOT EXISTS billing_auto_charge_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    service_id UUID NOT NULL REFERENCES billing_service_master(id),
    trigger_type VARCHAR(50) NOT NULL,
    trigger_interval_hours INTEGER,
    applies_to_bill_type VARCHAR(20),
    use_tariff_pricing BOOLEAN DEFAULT TRUE,
    fixed_price NUMERIC(12,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 23. Payee Change Logs
CREATE TABLE IF NOT EXISTS billing_payee_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    patient_id UUID NOT NULL,
    encounter_id UUID NOT NULL,
    bill_id UUID NOT NULL,
    old_payer_type VARCHAR(50) NOT NULL,
    new_payer_type VARCHAR(50) NOT NULL,
    old_insurance_id UUID,
    new_insurance_id UUID,
    old_corporate_id UUID,
    new_corporate_id UUID,
    reason TEXT,
    recalculation_done BOOLEAN DEFAULT FALSE,
    changed_by UUID NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT 'Sprint 1 Billing Masters: 23 tables created successfully!' AS result;
