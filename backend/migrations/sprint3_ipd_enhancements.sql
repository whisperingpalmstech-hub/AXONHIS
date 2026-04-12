-- Sprint 3: IPD Enhancements (FRD Gaps 2-4)

CREATE TABLE IF NOT EXISTS ipd_admission_estimates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), org_id UUID NOT NULL,
    admission_request_id UUID, patient_id UUID, patient_name VARCHAR(255) NOT NULL,
    bed_category VARCHAR(100), expected_stay_days INTEGER DEFAULT 3, package_id UUID,
    estimated_room_charges NUMERIC(12,2) DEFAULT 0, estimated_procedure_charges NUMERIC(12,2) DEFAULT 0,
    estimated_pharmacy_charges NUMERIC(12,2) DEFAULT 0, estimated_lab_charges NUMERIC(12,2) DEFAULT 0,
    estimated_misc_charges NUMERIC(12,2) DEFAULT 0, total_estimated_cost NUMERIC(14,2) DEFAULT 0,
    deposit_required NUMERIC(12,2) DEFAULT 0, insurance_coverage NUMERIC(12,2) DEFAULT 0,
    patient_liability NUMERIC(12,2) DEFAULT 0, estimation_details JSONB,
    status VARCHAR(30) DEFAULT 'draft', created_by UUID NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ipd_pre_authorizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), org_id UUID NOT NULL,
    admission_id UUID, patient_id UUID NOT NULL, insurance_detail_id UUID,
    pre_auth_number VARCHAR(100), requested_amount NUMERIC(14,2) NOT NULL,
    approved_amount NUMERIC(14,2), status VARCHAR(30) DEFAULT 'pending',
    diagnosis_codes JSONB, procedure_codes JSONB, expected_stay_days INTEGER,
    bed_category VARCHAR(100), remarks TEXT, response_notes TEXT,
    requested_by UUID NOT NULL, requested_at TIMESTAMPTZ DEFAULT NOW(),
    responded_at TIMESTAMPTZ, expires_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS ipd_discharge_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), org_id UUID NOT NULL,
    admission_id UUID NOT NULL, patient_id UUID NOT NULL,
    summary_number VARCHAR(50) UNIQUE NOT NULL,
    admission_diagnosis TEXT, discharge_diagnosis TEXT, clinical_summary TEXT,
    hospital_course TEXT, procedures_performed JSONB, investigation_results JSONB,
    condition_at_discharge VARCHAR(100), discharge_medications JSONB,
    diet_instructions TEXT, activity_restrictions TEXT, wound_care TEXT,
    follow_up_instructions JSONB, warning_signs TEXT, referrals JSONB,
    discharge_type VARCHAR(50) DEFAULT 'normal', death_summary TEXT, lama_reason TEXT,
    status VARCHAR(30) DEFAULT 'draft', prepared_by UUID NOT NULL,
    reviewed_by UUID, approved_by UUID, approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS ipd_diet_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), org_id UUID NOT NULL,
    admission_id UUID NOT NULL, patient_id UUID NOT NULL,
    diet_type VARCHAR(50) NOT NULL, special_instructions TEXT, allergies TEXT,
    meal_preference VARCHAR(20) DEFAULT 'veg', texture VARCHAR(30),
    fluid_restriction VARCHAR(50), supplements JSONB,
    start_date TIMESTAMPTZ DEFAULT NOW(), end_date TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE, ordered_by UUID NOT NULL,
    ordered_by_name VARCHAR(255), created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ipd_consent_forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), org_id UUID NOT NULL,
    admission_id UUID NOT NULL, patient_id UUID NOT NULL,
    consent_type VARCHAR(50) NOT NULL, consent_template_id UUID,
    consent_details TEXT, procedure_name VARCHAR(255),
    risks_explained BOOLEAN DEFAULT FALSE, alternatives_explained BOOLEAN DEFAULT FALSE,
    patient_signature TEXT, witness_name VARCHAR(255), witness_signature TEXT,
    obtained_by UUID NOT NULL, obtained_by_name VARCHAR(255),
    status VARCHAR(30) DEFAULT 'pending', signed_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ, created_at TIMESTAMPTZ DEFAULT NOW()
);

SELECT 'Sprint 3 IPD Enhancements: 5 tables created!' AS result;
