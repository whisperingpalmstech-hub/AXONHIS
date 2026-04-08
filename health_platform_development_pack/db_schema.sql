
-- Unified Clinical Practice + Health ATM Platform
-- Baseline PostgreSQL-oriented schema
-- This is a conceptual implementation starter, not a final migration pack.

create extension if not exists "uuid-ossp";

create table organization (
    organization_id uuid primary key default uuid_generate_v4(),
    code varchar(50) unique not null,
    name varchar(255) not null,
    parent_organization_id uuid references organization(organization_id),
    organization_type varchar(50) not null,
    status varchar(30) not null default 'ACTIVE',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table facility (
    facility_id uuid primary key default uuid_generate_v4(),
    organization_id uuid not null references organization(organization_id),
    code varchar(50) not null,
    name varchar(255) not null,
    facility_type varchar(50) not null,
    timezone varchar(64),
    status varchar(30) not null default 'ACTIVE',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (organization_id, code)
);

create table specialty_profile (
    specialty_profile_id uuid primary key default uuid_generate_v4(),
    code varchar(50) unique not null,
    name varchar(255) not null,
    version_no integer not null default 1,
    description text,
    ui_config_json jsonb not null default '{}'::jsonb,
    history_template_json jsonb not null default '{}'::jsonb,
    exam_template_json jsonb not null default '{}'::jsonb,
    ai_config_json jsonb not null default '{}'::jsonb,
    document_template_json jsonb not null default '{}'::jsonb,
    active_flag boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table clinician (
    clinician_id uuid primary key default uuid_generate_v4(),
    organization_id uuid not null references organization(organization_id),
    facility_id uuid references facility(facility_id),
    specialty_profile_id uuid references specialty_profile(specialty_profile_id),
    code varchar(50),
    display_name varchar(255) not null,
    mobile_number varchar(30),
    email varchar(255),
    clinician_type varchar(50) not null default 'DOCTOR',
    active_flag boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table patient (
    patient_id uuid primary key default uuid_generate_v4(),
    enterprise_patient_key varchar(100) unique not null,
    organization_id uuid not null references organization(organization_id),
    mrn varchar(100),
    first_name varchar(100),
    last_name varchar(100),
    display_name varchar(255) not null,
    dob date,
    sex varchar(20),
    mobile_number varchar(30),
    email varchar(255),
    preferred_language varchar(30),
    deceased_flag boolean not null default false,
    status varchar(30) not null default 'ACTIVE',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table patient_identifier (
    patient_identifier_id uuid primary key default uuid_generate_v4(),
    patient_id uuid not null references patient(patient_id) on delete cascade,
    identifier_type varchar(50) not null,
    identifier_value varchar(255) not null,
    issuing_authority varchar(255),
    active_flag boolean not null default true,
    verified_flag boolean not null default false,
    created_at timestamptz not null default now(),
    unique (identifier_type, identifier_value)
);

create table consent_profile (
    consent_profile_id uuid primary key default uuid_generate_v4(),
    patient_id uuid not null unique references patient(patient_id) on delete cascade,
    default_share_mode varchar(30) not null default 'ASK_EACH_TIME',
    allow_summary_share boolean not null default true,
    allow_full_record_share boolean not null default false,
    sensitive_category_rules jsonb not null default '{}'::jsonb,
    marketing_contact_allowed boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table channel (
    channel_id uuid primary key default uuid_generate_v4(),
    organization_id uuid not null references organization(organization_id),
    facility_id uuid references facility(facility_id),
    code varchar(50) not null,
    name varchar(255) not null,
    channel_type varchar(50) not null,
    status varchar(30) not null default 'ACTIVE',
    unique (organization_id, code)
);

create table appointment (
    appointment_id uuid primary key default uuid_generate_v4(),
    organization_id uuid not null references organization(organization_id),
    facility_id uuid references facility(facility_id),
    channel_id uuid references channel(channel_id),
    patient_id uuid not null references patient(patient_id),
    clinician_id uuid references clinician(clinician_id),
    specialty_profile_id uuid references specialty_profile(specialty_profile_id),
    appointment_mode varchar(30) not null,
    appointment_type varchar(30) not null,
    slot_start timestamptz not null,
    slot_end timestamptz not null,
    booking_source varchar(50),
    status varchar(30) not null default 'BOOKED',
    reason_text text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table encounter (
    encounter_id uuid primary key default uuid_generate_v4(),
    organization_id uuid not null references organization(organization_id),
    facility_id uuid references facility(facility_id),
    appointment_id uuid references appointment(appointment_id),
    patient_id uuid not null references patient(patient_id),
    clinician_id uuid references clinician(clinician_id),
    specialty_profile_id uuid references specialty_profile(specialty_profile_id),
    encounter_mode varchar(30) not null,
    encounter_status varchar(30) not null default 'OPEN',
    chief_complaint text,
    started_at timestamptz not null default now(),
    closed_at timestamptz,
    created_by varchar(100),
    updated_at timestamptz not null default now()
);

create table encounter_note (
    encounter_note_id uuid primary key default uuid_generate_v4(),
    encounter_id uuid not null references encounter(encounter_id) on delete cascade,
    note_type varchar(50) not null,
    structured_json jsonb not null default '{}'::jsonb,
    narrative_text text,
    authored_by varchar(100),
    authored_at timestamptz not null default now()
);

create table diagnosis (
    diagnosis_id uuid primary key default uuid_generate_v4(),
    encounter_id uuid not null references encounter(encounter_id) on delete cascade,
    diagnosis_type varchar(30) not null,
    diagnosis_code varchar(50),
    diagnosis_display varchar(255) not null,
    probability_score numeric(6,3),
    source_type varchar(30) not null default 'CLINICIAN',
    accepted_flag boolean not null default true,
    created_at timestamptz not null default now()
);

create table service_request (
    service_request_id uuid primary key default uuid_generate_v4(),
    encounter_id uuid not null references encounter(encounter_id) on delete cascade,
    request_type varchar(30) not null,
    catalog_code varchar(100),
    catalog_name varchar(255) not null,
    priority varchar(30),
    status varchar(30) not null default 'ORDERED',
    request_payload_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table medication_request (
    medication_request_id uuid primary key default uuid_generate_v4(),
    encounter_id uuid not null references encounter(encounter_id) on delete cascade,
    medication_code varchar(100),
    medication_name varchar(255) not null,
    route varchar(100),
    dose varchar(100),
    frequency varchar(100),
    duration varchar(100),
    otc_flag boolean not null default false,
    formulary_flag boolean not null default true,
    source_type varchar(30) not null default 'CLINICIAN',
    created_at timestamptz not null default now()
);

create table device (
    device_id uuid primary key default uuid_generate_v4(),
    organization_id uuid not null references organization(organization_id),
    facility_id uuid references facility(facility_id),
    device_code varchar(100) not null,
    device_name varchar(255) not null,
    device_class varchar(100) not null,
    manufacturer varchar(255),
    integration_method varchar(30),
    status varchar(30) not null default 'ACTIVE',
    metadata_json jsonb not null default '{}'::jsonb,
    unique (organization_id, device_code)
);

create table device_result (
    device_result_id uuid primary key default uuid_generate_v4(),
    encounter_id uuid not null references encounter(encounter_id) on delete cascade,
    device_id uuid not null references device(device_id),
    operator_user_ref varchar(100),
    result_type varchar(50) not null,
    payload_json jsonb not null default '{}'::jsonb,
    raw_uri text,
    interpretation_status varchar(30) not null default 'UNREVIEWED',
    captured_at timestamptz not null default now()
);

create table observation (
    observation_id uuid primary key default uuid_generate_v4(),
    encounter_id uuid not null references encounter(encounter_id) on delete cascade,
    device_result_id uuid references device_result(device_result_id),
    observation_code varchar(100) not null,
    observation_display varchar(255) not null,
    value_text varchar(255),
    value_numeric numeric(18,4),
    unit varchar(50),
    status varchar(30) not null default 'FINAL',
    effective_at timestamptz not null default now()
);

create table document (
    document_id uuid primary key default uuid_generate_v4(),
    patient_id uuid not null references patient(patient_id) on delete cascade,
    encounter_id uuid references encounter(encounter_id),
    document_type varchar(50) not null,
    title varchar(255) not null,
    storage_uri text not null,
    mime_type varchar(100),
    sensitive_flag boolean not null default false,
    share_sensitivity varchar(30) not null default 'STANDARD',
    created_by varchar(100),
    created_at timestamptz not null default now()
);

create table share_grant (
    share_grant_id uuid primary key default uuid_generate_v4(),
    patient_id uuid not null references patient(patient_id) on delete cascade,
    grant_method varchar(30) not null,
    grantee_type varchar(30) not null,
    grantee_reference varchar(255),
    scope_type varchar(30) not null,
    scope_json jsonb not null default '{}'::jsonb,
    qr_token varchar(255) unique,
    secure_link_token varchar(255) unique,
    expires_at timestamptz,
    revoked_at timestamptz,
    created_at timestamptz not null default now()
);

create table share_access_log (
    share_access_log_id uuid primary key default uuid_generate_v4(),
    share_grant_id uuid not null references share_grant(share_grant_id) on delete cascade,
    accessed_by varchar(255),
    access_channel varchar(30),
    access_result varchar(30) not null,
    accessed_at timestamptz not null default now(),
    metadata_json jsonb not null default '{}'::jsonb
);

create table payer (
    payer_id uuid primary key default uuid_generate_v4(),
    organization_id uuid not null references organization(organization_id),
    payer_code varchar(100) not null,
    payer_name varchar(255) not null,
    payer_type varchar(50) not null,
    active_flag boolean not null default true,
    unique (organization_id, payer_code)
);

create table coverage (
    coverage_id uuid primary key default uuid_generate_v4(),
    patient_id uuid not null references patient(patient_id) on delete cascade,
    payer_id uuid not null references payer(payer_id),
    policy_number varchar(255),
    member_reference varchar(255),
    plan_name varchar(255),
    effective_from date,
    effective_to date,
    active_flag boolean not null default true,
    created_at timestamptz not null default now()
);

create table billing_invoice (
    billing_invoice_id uuid primary key default uuid_generate_v4(),
    organization_id uuid not null references organization(organization_id),
    patient_id uuid not null references patient(patient_id),
    encounter_id uuid references encounter(encounter_id),
    coverage_id uuid references coverage(coverage_id),
    invoice_number varchar(100) not null unique,
    currency_code varchar(10) not null default 'USD',
    total_amount numeric(18,2) not null default 0,
    status varchar(30) not null default 'DRAFT',
    created_at timestamptz not null default now()
);

create table billing_line_item (
    billing_line_item_id uuid primary key default uuid_generate_v4(),
    billing_invoice_id uuid not null references billing_invoice(billing_invoice_id) on delete cascade,
    line_type varchar(30) not null,
    catalog_reference varchar(100),
    description varchar(255) not null,
    quantity numeric(18,2) not null default 1,
    unit_price numeric(18,2) not null default 0,
    line_amount numeric(18,2) not null default 0
);

create table integration_event (
    integration_event_id uuid primary key default uuid_generate_v4(),
    organization_id uuid references organization(organization_id),
    source_system varchar(100) not null,
    target_system varchar(100),
    resource_type varchar(50) not null,
    resource_id varchar(255),
    event_type varchar(50) not null,
    event_status varchar(30) not null default 'PENDING',
    payload_json jsonb not null default '{}'::jsonb,
    correlation_id varchar(100),
    created_at timestamptz not null default now()
);

create table audit_event (
    audit_event_id uuid primary key default uuid_generate_v4(),
    organization_id uuid references organization(organization_id),
    actor_ref varchar(100),
    actor_role varchar(50),
    patient_id uuid references patient(patient_id),
    encounter_id uuid references encounter(encounter_id),
    action_type varchar(100) not null,
    action_status varchar(30) not null,
    event_time timestamptz not null default now(),
    details_json jsonb not null default '{}'::jsonb
);

create index idx_patient_mobile on patient(mobile_number);
create index idx_appointment_slot on appointment(slot_start, slot_end);
create index idx_encounter_patient on encounter(patient_id, started_at desc);
create index idx_document_patient on document(patient_id, created_at desc);
create index idx_device_result_encounter on device_result(encounter_id, captured_at desc);
create index idx_integration_event_status on integration_event(event_status, created_at desc);
create index idx_audit_event_time on audit_event(event_time desc);
