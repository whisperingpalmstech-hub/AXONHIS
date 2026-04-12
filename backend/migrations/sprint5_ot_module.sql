-- Sprint 5: Operating Theatre (OT) Module

CREATE TABLE IF NOT EXISTS ot_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), org_id UUID NOT NULL,
    room_code VARCHAR(50) NOT NULL, room_name VARCHAR(255) NOT NULL,
    room_type VARCHAR(50) DEFAULT 'general', floor VARCHAR(50),
    is_laminar_flow BOOLEAN DEFAULT FALSE, has_c_arm BOOLEAN DEFAULT FALSE,
    has_laser BOOLEAN DEFAULT FALSE, status VARCHAR(30) DEFAULT 'available',
    is_active BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS ix_ot_rooms_org ON ot_rooms(org_id);

CREATE TABLE IF NOT EXISTS ot_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), org_id UUID NOT NULL,
    ot_room_id UUID NOT NULL REFERENCES ot_rooms(id),
    patient_id UUID NOT NULL, patient_name VARCHAR(255) NOT NULL,
    patient_uhid VARCHAR(50), admission_id UUID, encounter_id UUID,
    surgery_name VARCHAR(500) NOT NULL, surgery_code VARCHAR(50),
    surgery_type VARCHAR(50) DEFAULT 'elective', laterality VARCHAR(20),
    estimated_duration_mins INTEGER DEFAULT 60, anesthesia_type VARCHAR(50),
    scheduled_date TIMESTAMPTZ NOT NULL, scheduled_end TIMESTAMPTZ,
    actual_start TIMESTAMPTZ, actual_end TIMESTAMPTZ,
    primary_surgeon_id UUID NOT NULL, primary_surgeon_name VARCHAR(255) NOT NULL,
    assistant_surgeons JSONB, anesthesiologist_name VARCHAR(255),
    scrub_nurse_name VARCHAR(255), pre_op_diagnosis TEXT,
    consent_obtained BOOLEAN DEFAULT FALSE, pre_op_checklist JSONB,
    blood_group VARCHAR(10), blood_units_reserved INTEGER DEFAULT 0,
    status VARCHAR(30) DEFAULT 'scheduled', cancellation_reason TEXT,
    post_op_diagnosis TEXT, post_op_notes TEXT, complications JSONB,
    specimens JSONB, implants_used JSONB, blood_loss_ml INTEGER,
    total_charges NUMERIC(14,2) DEFAULT 0,
    created_by UUID NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_ot_sched_org ON ot_schedules(org_id);

CREATE TABLE IF NOT EXISTS ot_consumables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), org_id UUID NOT NULL,
    ot_schedule_id UUID NOT NULL REFERENCES ot_schedules(id),
    item_name VARCHAR(255) NOT NULL, item_code VARCHAR(50), item_id UUID,
    quantity INTEGER DEFAULT 1, unit_price NUMERIC(12,2) DEFAULT 0,
    total_price NUMERIC(12,2) DEFAULT 0, category VARCHAR(50),
    is_returned BOOLEAN DEFAULT FALSE, recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ot_anesthesia_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), org_id UUID NOT NULL,
    ot_schedule_id UUID NOT NULL REFERENCES ot_schedules(id),
    anesthesia_type VARCHAR(50) NOT NULL, asa_score VARCHAR(10),
    airway VARCHAR(50), induction_time TIMESTAMPTZ, extubation_time TIMESTAMPTZ,
    medications_given JSONB, vital_signs_log JSONB,
    complications TEXT, notes TEXT,
    recorded_by UUID NOT NULL, recorded_by_name VARCHAR(255)
);

SELECT 'Sprint 5 OT Module: 4 tables created!' AS result;
