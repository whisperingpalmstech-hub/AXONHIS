-- Sprint 2: Emergency Room (ER) Module
-- FRD Reference: HIMS_ER_Module_FRD.docx

CREATE TABLE IF NOT EXISTS er_encounters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    er_number VARCHAR(50) UNIQUE NOT NULL,
    registration_type VARCHAR(20) DEFAULT 'normal',
    patient_id UUID,
    encounter_id UUID,
    patient_name VARCHAR(255) NOT NULL,
    patient_uhid VARCHAR(50),
    age INTEGER,
    age_unit VARCHAR(10) DEFAULT 'years',
    gender VARCHAR(20),
    mobile VARCHAR(20),
    temp_id_description TEXT,
    mode_of_arrival VARCHAR(50),
    ambulance_number VARCHAR(50),
    brought_by VARCHAR(255),
    referral_source VARCHAR(255),
    chief_complaint TEXT,
    presenting_complaints JSONB,
    status VARCHAR(50) DEFAULT 'registered',
    zone VARCHAR(20),
    priority VARCHAR(30),
    is_mlc BOOLEAN DEFAULT FALSE,
    is_critical BOOLEAN DEFAULT FALSE,
    is_ventilator BOOLEAN DEFAULT FALSE,
    is_allergy BOOLEAN DEFAULT FALSE,
    allergy_details TEXT,
    has_overdue_orders BOOLEAN DEFAULT FALSE,
    has_overdue_los BOOLEAN DEFAULT FALSE,
    attending_doctor_id UUID,
    attending_doctor_name VARCHAR(255),
    attending_nurse_id UUID,
    attending_nurse_name VARCHAR(255),
    arrival_time TIMESTAMPTZ DEFAULT NOW(),
    triage_time TIMESTAMPTZ,
    treatment_start_time TIMESTAMPTZ,
    discharge_time TIMESTAMPTZ,
    disposition VARCHAR(50),
    disposition_department VARCHAR(100),
    ipd_admission_id UUID,
    bill_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_er_enc_org ON er_encounters(org_id);
CREATE INDEX IF NOT EXISTS ix_er_enc_patient ON er_encounters(patient_id);
CREATE INDEX IF NOT EXISTS ix_er_enc_status ON er_encounters(status);

CREATE TABLE IF NOT EXISTS er_triage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    er_encounter_id UUID NOT NULL REFERENCES er_encounters(id),
    triage_category VARCHAR(30) NOT NULL,
    triage_color VARCHAR(20),
    temperature NUMERIC(5,2),
    pulse INTEGER,
    bp_systolic INTEGER,
    bp_diastolic INTEGER,
    respiratory_rate INTEGER,
    spo2 NUMERIC(5,2),
    gcs_score INTEGER,
    pain_score INTEGER,
    blood_glucose NUMERIC(7,2),
    airway VARCHAR(50),
    breathing VARCHAR(50),
    circulation VARCHAR(50),
    disability VARCHAR(50),
    exposure VARCHAR(50),
    allergies TEXT,
    current_medications TEXT,
    past_medical_history TEXT,
    last_meal VARCHAR(100),
    immunization_status VARCHAR(100),
    triage_notes TEXT,
    triaged_by UUID NOT NULL,
    triaged_by_name VARCHAR(255),
    triaged_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS er_beds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    bed_code VARCHAR(50) NOT NULL,
    zone VARCHAR(20) NOT NULL,
    bed_type VARCHAR(50) DEFAULT 'stretcher',
    is_monitored BOOLEAN DEFAULT FALSE,
    has_ventilator BOOLEAN DEFAULT FALSE,
    status VARCHAR(30) DEFAULT 'available',
    occupied_by_er_encounter_id UUID,
    patient_gender VARCHAR(20),
    occupied_since TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS ix_er_beds_org ON er_beds(org_id);

CREATE TABLE IF NOT EXISTS er_mlc_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    er_encounter_id UUID NOT NULL REFERENCES er_encounters(id),
    mlc_number VARCHAR(50) UNIQUE NOT NULL,
    mlc_type VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'medium',
    police_station VARCHAR(255),
    police_officer_name VARCHAR(255),
    police_officer_badge VARCHAR(100),
    fir_number VARCHAR(100),
    buckle_number VARCHAR(100),
    injury_description TEXT,
    injury_details JSONB,
    legal_notes TEXT,
    documents JSONB,
    status VARCHAR(30) DEFAULT 'active',
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS er_nursing_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    er_encounter_id UUID NOT NULL REFERENCES er_encounters(id),
    score_type VARCHAR(30) NOT NULL,
    total_score INTEGER NOT NULL,
    risk_level VARCHAR(30),
    score_components JSONB,
    interpretation TEXT,
    scored_by UUID NOT NULL,
    scored_by_name VARCHAR(255),
    scored_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS er_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    er_encounter_id UUID NOT NULL REFERENCES er_encounters(id),
    order_type VARCHAR(30) NOT NULL,
    order_id UUID,
    order_description TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'stat',
    status VARCHAR(30) DEFAULT 'ordered',
    ordered_by UUID NOT NULL,
    ordered_by_name VARCHAR(255),
    ordered_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

SELECT 'Sprint 2 ER Module: 6 tables created successfully!' AS result;
