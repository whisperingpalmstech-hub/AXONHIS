-- Sprint 4: Cross-Module Integration Bridge

CREATE TABLE IF NOT EXISTS cross_module_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), org_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL, source_module VARCHAR(50) NOT NULL,
    target_module VARCHAR(50) NOT NULL, source_id UUID NOT NULL,
    target_id UUID, patient_id UUID, payload JSONB,
    status VARCHAR(30) DEFAULT 'completed', error_message TEXT,
    triggered_by UUID NOT NULL, triggered_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_cme_org ON cross_module_events(org_id);

CREATE TABLE IF NOT EXISTS charge_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), org_id UUID NOT NULL,
    patient_id UUID NOT NULL, encounter_type VARCHAR(20) NOT NULL,
    encounter_id UUID NOT NULL, service_id UUID, service_code VARCHAR(50),
    service_name VARCHAR(255) NOT NULL, service_group VARCHAR(100),
    source_module VARCHAR(50) NOT NULL, source_order_id UUID,
    quantity INTEGER DEFAULT 1, unit_price NUMERIC(12,2) NOT NULL,
    discount_amount NUMERIC(12,2) DEFAULT 0, tax_amount NUMERIC(12,2) DEFAULT 0,
    net_amount NUMERIC(12,2) NOT NULL, is_stat BOOLEAN DEFAULT FALSE,
    stat_surcharge NUMERIC(12,2) DEFAULT 0, tariff_plan_id UUID,
    is_billed BOOLEAN DEFAULT FALSE, bill_id UUID,
    is_cancelled BOOLEAN DEFAULT FALSE, cancelled_reason TEXT,
    posted_by UUID NOT NULL, posted_by_name VARCHAR(255),
    posted_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_cp_org ON charge_postings(org_id);
CREATE INDEX IF NOT EXISTS ix_cp_patient ON charge_postings(patient_id);
CREATE INDEX IF NOT EXISTS ix_cp_encounter ON charge_postings(encounter_id);

CREATE TABLE IF NOT EXISTS patient_ledgers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), org_id UUID NOT NULL,
    patient_id UUID NOT NULL, encounter_type VARCHAR(20) NOT NULL,
    encounter_id UUID NOT NULL,
    total_charges NUMERIC(14,2) DEFAULT 0, total_discounts NUMERIC(14,2) DEFAULT 0,
    total_tax NUMERIC(14,2) DEFAULT 0, total_deposits NUMERIC(14,2) DEFAULT 0,
    total_payments NUMERIC(14,2) DEFAULT 0, total_insurance_covered NUMERIC(14,2) DEFAULT 0,
    outstanding_balance NUMERIC(14,2) DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_pl_org ON patient_ledgers(org_id);
CREATE INDEX IF NOT EXISTS ix_pl_patient ON patient_ledgers(patient_id);

SELECT 'Sprint 4 Integration: 3 tables created!' AS result;
