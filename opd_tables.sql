-- OPD Pre-Registrations
CREATE TABLE IF NOT EXISTS opd_pre_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pre_reg_id VARCHAR(30) UNIQUE NOT NULL,
    org_id UUID,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    gender VARCHAR(20),
    date_of_birth DATE,
    mobile_number VARCHAR(20) NOT NULL,
    email VARCHAR(150),
    address_line VARCHAR(300),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    nok_name VARCHAR(100),
    nok_relationship VARCHAR(50),
    nok_phone VARCHAR(20),
    payer_category VARCHAR(50),
    insurance_provider VARCHAR(200),
    policy_number VARCHAR(100),
    appointment_id UUID,
    preferred_doctor_id UUID,
    preferred_department VARCHAR(100),
    preferred_date DATE,
    status VARCHAR(30) DEFAULT 'pending' NOT NULL,
    converted_patient_id UUID,
    converted_uhid VARCHAR(50),
    duplicate_score FLOAT,
    potential_duplicate_id UUID,
    photo_url VARCHAR(500),
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_prereg_mobile ON opd_pre_registrations(mobile_number);
CREATE INDEX IF NOT EXISTS ix_prereg_status ON opd_pre_registrations(status);
CREATE INDEX IF NOT EXISTS ix_prereg_org ON opd_pre_registrations(org_id);

-- OPD Deposits
CREATE TABLE IF NOT EXISTS opd_deposits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deposit_number VARCHAR(30) UNIQUE NOT NULL,
    org_id UUID,
    patient_id UUID NOT NULL,
    visit_id UUID,
    deposit_amount NUMERIC(12,2) NOT NULL,
    consumed_amount NUMERIC(12,2) DEFAULT 0.00,
    balance_amount NUMERIC(12,2) NOT NULL,
    refunded_amount NUMERIC(12,2) DEFAULT 0.00,
    payment_mode VARCHAR(50) NOT NULL,
    transaction_reference VARCHAR(200),
    receipt_number VARCHAR(50),
    status VARCHAR(30) DEFAULT 'active' NOT NULL,
    collected_by UUID NOT NULL,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    refund_reason TEXT,
    refunded_by UUID,
    refunded_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_deposit_patient ON opd_deposits(patient_id);

-- OPD Deposit Consumptions
CREATE TABLE IF NOT EXISTS opd_deposit_consumptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deposit_id UUID NOT NULL REFERENCES opd_deposits(id),
    bill_id UUID NOT NULL,
    consumed_amount NUMERIC(12,2) NOT NULL,
    consumed_at TIMESTAMPTZ DEFAULT NOW(),
    consumed_by UUID NOT NULL,
    notes TEXT
);

-- OPD Consent Templates
CREATE TABLE IF NOT EXISTS opd_consent_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID,
    template_name VARCHAR(200) NOT NULL,
    template_category VARCHAR(100) NOT NULL,
    template_body TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- OPD Consent Documents
CREATE TABLE IF NOT EXISTS opd_consent_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID,
    consent_number VARCHAR(30) UNIQUE NOT NULL,
    patient_id UUID NOT NULL,
    visit_id UUID,
    template_id UUID REFERENCES opd_consent_templates(id),
    consent_title VARCHAR(200) NOT NULL,
    consent_body TEXT NOT NULL,
    status VARCHAR(30) DEFAULT 'draft' NOT NULL,
    signature_data TEXT,
    signed_by_name VARCHAR(200),
    signed_at TIMESTAMPTZ,
    witness_name VARCHAR(200),
    witness_designation VARCHAR(100),
    pdf_url VARCHAR(500),
    emailed_to VARCHAR(200),
    emailed_at TIMESTAMPTZ,
    printed_at TIMESTAMPTZ,
    scanned_document_url VARCHAR(500),
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- OPD Pro-Forma Bills
CREATE TABLE IF NOT EXISTS opd_proforma_bills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID,
    proforma_number VARCHAR(30) UNIQUE NOT NULL,
    patient_id UUID NOT NULL,
    visit_id UUID,
    items JSONB DEFAULT '[]',
    subtotal NUMERIC(12,2) DEFAULT 0.00,
    tax_amount NUMERIC(12,2) DEFAULT 0.00,
    discount_amount NUMERIC(12,2) DEFAULT 0.00,
    estimated_total NUMERIC(12,2) DEFAULT 0.00,
    valid_until DATE,
    notes TEXT,
    converted_to_bill_id UUID,
    generated_by UUID NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- OPD Kiosk Check-ins
CREATE TABLE IF NOT EXISTS opd_kiosk_checkins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID,
    kiosk_id VARCHAR(50),
    verification_method VARCHAR(30) NOT NULL,
    verification_data VARCHAR(200),
    patient_id UUID,
    appointment_id UUID,
    visit_id UUID,
    status VARCHAR(30) DEFAULT 'started' NOT NULL,
    token_number VARCHAR(20),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

-- OPD Patient Notifications
CREATE TABLE IF NOT EXISTS opd_patient_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID,
    patient_id UUID NOT NULL,
    visit_id UUID,
    notification_type VARCHAR(50) NOT NULL,
    channel VARCHAR(30) NOT NULL,
    recipient VARCHAR(200) NOT NULL,
    title VARCHAR(200),
    message TEXT NOT NULL,
    extra_data JSONB DEFAULT '{}',
    status VARCHAR(30) DEFAULT 'sent',
    sent_at TIMESTAMPTZ DEFAULT NOW()
);

-- OPD Waitlist
CREATE TABLE IF NOT EXISTS opd_waitlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID,
    patient_id UUID NOT NULL,
    doctor_id UUID NOT NULL,
    department VARCHAR(100) NOT NULL,
    preferred_date DATE NOT NULL,
    preferred_time_start VARCHAR(10),
    preferred_time_end VARCHAR(10),
    reason TEXT,
    priority INTEGER DEFAULT 5,
    status VARCHAR(30) DEFAULT 'waiting',
    offered_slot_id UUID,
    notified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- AI Scheduling Predictions
CREATE TABLE IF NOT EXISTS opd_ai_scheduling_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID,
    booking_id UUID,
    patient_id UUID NOT NULL,
    doctor_id UUID NOT NULL,
    appointment_date DATE NOT NULL,
    no_show_probability FLOAT DEFAULT 0.0,
    prediction_factors JSONB DEFAULT '[]',
    recommendation VARCHAR(50),
    recommendation_applied BOOLEAN DEFAULT FALSE,
    predicted_at TIMESTAMPTZ DEFAULT NOW()
);

-- OPD Daily Analytics
CREATE TABLE IF NOT EXISTS opd_daily_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID,
    analytics_date DATE NOT NULL,
    total_appointments INTEGER DEFAULT 0,
    total_walkins INTEGER DEFAULT 0,
    total_checkins INTEGER DEFAULT 0,
    total_visits INTEGER DEFAULT 0,
    completed_visits INTEGER DEFAULT 0,
    cancelled_visits INTEGER DEFAULT 0,
    no_show_count INTEGER DEFAULT 0,
    avg_wait_time_min FLOAT,
    max_wait_time_min FLOAT,
    median_wait_time_min FLOAT,
    avg_consultation_duration_min FLOAT,
    doctor_utilization JSONB DEFAULT '{}',
    total_revenue NUMERIC(14,2) DEFAULT 0.00,
    consultation_revenue NUMERIC(14,2) DEFAULT 0.00,
    diagnostic_revenue NUMERIC(14,2) DEFAULT 0.00,
    pharmacy_revenue NUMERIC(14,2) DEFAULT 0.00,
    total_deposits NUMERIC(14,2) DEFAULT 0.00,
    total_refunds NUMERIC(14,2) DEFAULT 0.00,
    department_breakdown JSONB DEFAULT '{}',
    peak_hour VARCHAR(10),
    hourly_distribution JSONB DEFAULT '{}',
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(analytics_date, org_id)
);

-- Bill Cancellation Audit Logs
CREATE TABLE IF NOT EXISTS opd_bill_cancellation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID,
    bill_id UUID NOT NULL,
    bill_number VARCHAR(50) NOT NULL,
    patient_id UUID NOT NULL,
    original_amount NUMERIC(12,2) NOT NULL,
    cancellation_reason TEXT NOT NULL,
    cancelled_by UUID NOT NULL,
    authorized_by UUID,
    cancelled_at TIMESTAMPTZ DEFAULT NOW(),
    supporting_document_url VARCHAR(500)
);
