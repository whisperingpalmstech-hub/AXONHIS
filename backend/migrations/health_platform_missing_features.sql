-- Health Platform Development Pack - Missing Features Migration
-- This migration adds tables for all missing features identified in the gap analysis
-- 
-- Features included:
-- 1. Event Bus (Integration Layer)
-- 2. Longitudinal Record Index (Workflow Layer)
-- 3. Clinical Rule Engine (Intelligence Layer)
-- 4. Device Adapter Framework (Integration Layer)
-- 5. Config Service (Future Autonomy)
-- 6. Approval Gates (Future Autonomy)
-- 7. Webhook Publisher (Integration Layer)
-- 8. Suggestion Tracker (Intelligence Layer)
-- 9. Prompt Mappings (Specialty UI)
-- 10. Document Template Mappings (Specialty UI)
-- 11. Doctor Preferences (Specialty UI)

-- ============================================================================
-- 1. EVENT BUS TABLES
-- ============================================================================

-- Event Bus main table for operational events
CREATE TABLE IF NOT EXISTS md_event (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    event_version VARCHAR(20) DEFAULT '1.0' NOT NULL,
    correlation_id VARCHAR(100),
    causation_id VARCHAR(100),
    source_system VARCHAR(50) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    aggregate_id UUID,
    aggregate_type VARCHAR(50),
    payload JSONB NOT NULL DEFAULT '{}',
    meta_data JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(30) DEFAULT 'PENDING' NOT NULL,
    retry_count NUMERIC(3,0) DEFAULT 0 NOT NULL,
    max_retries NUMERIC(3,0) DEFAULT 3 NOT NULL,
    error_message TEXT,
    processed_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Event subscription table for event consumers
CREATE TABLE IF NOT EXISTS md_event_subscription (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscriber_name VARCHAR(255) UNIQUE NOT NULL,
    subscriber_type VARCHAR(50) NOT NULL,
    event_types JSONB NOT NULL DEFAULT '[]',
    endpoint_url VARCHAR(500),
    queue_name VARCHAR(255),
    service_name VARCHAR(255),
    filter_rules JSONB NOT NULL DEFAULT '{}',
    retry_policy JSONB NOT NULL DEFAULT '{}',
    active_flag BOOLEAN DEFAULT TRUE NOT NULL,
    last_heartbeat TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Event delivery tracking table
CREATE TABLE IF NOT EXISTS md_event_delivery (
    delivery_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES md_event(event_id) ON DELETE CASCADE,
    subscription_id UUID NOT NULL REFERENCES md_event_subscription(subscription_id) ON DELETE CASCADE,
    status VARCHAR(30) DEFAULT 'PENDING' NOT NULL,
    delivery_attempts NUMERIC(3,0) DEFAULT 0 NOT NULL,
    last_attempt_at TIMESTAMP,
    delivered_at TIMESTAMP,
    error_message TEXT,
    response_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Dead letter queue for failed events
CREATE TABLE IF NOT EXISTS md_event_dead_letter (
    dead_letter_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_event_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_payload JSONB NOT NULL DEFAULT '{}',
    failure_reason TEXT NOT NULL,
    failure_count NUMERIC(3,0) NOT NULL,
    original_created_at TIMESTAMP NOT NULL,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    resolved BOOLEAN DEFAULT FALSE NOT NULL,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100)
);

-- Event Bus Indexes
CREATE INDEX idx_event_status_created ON md_event(status, created_at);
CREATE INDEX idx_event_type_status ON md_event(event_type, status);
CREATE INDEX idx_event_correlation ON md_event(correlation_id, created_at);
CREATE INDEX idx_delivery_event_subscription ON md_event_delivery(event_id, subscription_id);
CREATE INDEX idx_delivery_status ON md_event_delivery(status, created_at);
CREATE INDEX idx_dead_letter_resolved ON md_event_dead_letter(resolved, archived_at);
CREATE INDEX idx_dead_letter_type ON md_event_dead_letter(event_type);

-- ============================================================================
-- 2. LONGITUDINAL RECORD INDEX TABLES
-- ============================================================================

-- Longitudinal Record Index for fast retrieval across patient history
CREATE TABLE IF NOT EXISTS md_longitudinal_record_index (
    index_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES md_patient(patient_id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES md_encounter(encounter_id) ON DELETE CASCADE,
    record_type VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    record_date TIMESTAMP NOT NULL,
    record_data JSONB NOT NULL DEFAULT '{}',
    search_vector TEXT,
    tags JSONB NOT NULL DEFAULT '[]',
    relevance_score NUMERIC(5,2),
    facility_id UUID REFERENCES md_facility(facility_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Patient Timeline for chronological view of all clinical events
CREATE TABLE IF NOT EXISTS md_patient_timeline (
    timeline_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES md_patient(patient_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_date TIMESTAMP NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    source_system VARCHAR(50) NOT NULL,
    encounter_id UUID REFERENCES md_encounter(encounter_id),
    facility_id UUID REFERENCES md_facility(facility_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Cache for frequently searched patient records
CREATE TABLE IF NOT EXISTS md_record_search_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES md_patient(patient_id) ON DELETE CASCADE,
    search_key VARCHAR(255) NOT NULL,
    cache_data JSONB NOT NULL DEFAULT '{}',
    hit_count NUMERIC(10,0) DEFAULT 0 NOT NULL,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Longitudinal Indexes
CREATE INDEX idx_longitudinal_patient_date ON md_longitudinal_record_index(patient_id, record_date);
CREATE INDEX idx_longitudinal_type_date ON md_longitudinal_record_index(record_type, record_date);
CREATE INDEX idx_longitudinal_patient_type ON md_longitudinal_record_index(patient_id, record_type);
CREATE INDEX idx_timeline_patient_date ON md_patient_timeline(patient_id, event_date);
CREATE INDEX idx_timeline_type_date ON md_patient_timeline(event_type, event_date);
CREATE INDEX idx_cache_patient_key ON md_record_search_cache(patient_id, search_key);
CREATE INDEX idx_cache_expires ON md_record_search_cache(expires_at);

-- ============================================================================
-- 3. CLINICAL RULE ENGINE TABLES
-- ============================================================================

-- Clinical Rule Engine model
CREATE TABLE IF NOT EXISTS md_clinical_rule (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_code VARCHAR(100) UNIQUE NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    rule_description TEXT,
    rule_category VARCHAR(50) NOT NULL,
    rule_version VARCHAR(20) DEFAULT '1.0' NOT NULL,
    status VARCHAR(30) DEFAULT 'DRAFT' NOT NULL,
    severity VARCHAR(20) DEFAULT 'INFO' NOT NULL,
    trigger_type VARCHAR(50) NOT NULL,
    condition_expression JSONB NOT NULL DEFAULT '{}',
    action_config JSONB NOT NULL DEFAULT '{}',
    priority NUMERIC(3,0) DEFAULT 5 NOT NULL,
    specialty_profile_id UUID REFERENCES md_specialty_profile(specialty_profile_id),
    facility_id UUID REFERENCES md_facility(facility_id),
    requires_approval BOOLEAN DEFAULT FALSE NOT NULL,
    auto_execute BOOLEAN DEFAULT FALSE NOT NULL,
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    effective_from TIMESTAMP,
    effective_to TIMESTAMP
);

-- Rule execution tracking model
CREATE TABLE IF NOT EXISTS md_rule_execution (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID NOT NULL REFERENCES md_clinical_rule(rule_id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES md_patient(patient_id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES md_encounter(encounter_id) ON DELETE CASCADE,
    trigger_event VARCHAR(100) NOT NULL,
    trigger_data JSONB NOT NULL DEFAULT '{}',
    execution_status VARCHAR(30) NOT NULL,
    rule_matched BOOLEAN DEFAULT FALSE NOT NULL,
    action_taken JSONB NOT NULL DEFAULT '{}',
    error_message TEXT,
    execution_time_ms NUMERIC(10,2),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Rule alert model for displaying alerts to clinicians
CREATE TABLE IF NOT EXISTS md_rule_alert (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES md_rule_execution(execution_id) ON DELETE CASCADE,
    rule_id UUID NOT NULL REFERENCES md_clinical_rule(rule_id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES md_patient(patient_id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES md_encounter(encounter_id) ON DELETE CASCADE,
    alert_title VARCHAR(255) NOT NULL,
    alert_message TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    suggested_action TEXT,
    action_required BOOLEAN DEFAULT TRUE NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE NOT NULL,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP,
    dismissed BOOLEAN DEFAULT FALSE NOT NULL,
    dismissed_by VARCHAR(100),
    dismissed_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Rule variable model for defining reusable variables in rules
CREATE TABLE IF NOT EXISTS md_rule_variable (
    variable_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variable_name VARCHAR(100) UNIQUE NOT NULL,
    variable_type VARCHAR(50) NOT NULL,
    variable_value JSONB NOT NULL,
    description TEXT,
    category VARCHAR(50),
    is_system BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Clinical Rule Indexes
CREATE INDEX idx_rule_status_category ON md_clinical_rule(status, rule_category);
CREATE INDEX idx_rule_trigger_status ON md_clinical_rule(trigger_type, status);
CREATE INDEX idx_execution_patient_time ON md_rule_execution(patient_id, executed_at);
CREATE INDEX idx_execution_rule_time ON md_rule_execution(rule_id, executed_at);
CREATE INDEX idx_alert_patient_status ON md_rule_alert(patient_id, acknowledged, dismissed);
CREATE INDEX idx_alert_severity_time ON md_rule_alert(severity, created_at);

-- ============================================================================
-- 4. DEVICE ADAPTER FRAMEWORK TABLES
-- ============================================================================

-- Device Adapter model for integrating medical devices
CREATE TABLE IF NOT EXISTS md_device_adapter (
    adapter_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    adapter_name VARCHAR(255) UNIQUE NOT NULL,
    adapter_type VARCHAR(50) NOT NULL,
    protocol VARCHAR(50) NOT NULL,
    connection_config JSONB NOT NULL DEFAULT '{}',
    device_id UUID REFERENCES md_device(device_id),
    facility_id UUID REFERENCES md_facility(facility_id),
    status VARCHAR(30) DEFAULT 'INACTIVE' NOT NULL,
    last_heartbeat TIMESTAMP,
    last_error TEXT,
    data_mapping JSONB NOT NULL DEFAULT '{}',
    transformation_rules JSONB NOT NULL DEFAULT '[]',
    polling_interval_seconds INTEGER DEFAULT 30 NOT NULL,
    auto_reconnect BOOLEAN DEFAULT TRUE NOT NULL,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Device data model for storing raw and processed device data
CREATE TABLE IF NOT EXISTS md_device_data (
    data_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    adapter_id UUID NOT NULL REFERENCES md_device_adapter(adapter_id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES md_encounter(encounter_id) ON DELETE CASCADE,
    patient_id UUID REFERENCES md_patient(patient_id) ON DELETE CASCADE,
    raw_data JSONB NOT NULL DEFAULT '{}',
    processed_data JSONB NOT NULL DEFAULT '{}',
    observation_type VARCHAR(50) NOT NULL,
    data_quality_score NUMERIC(5,2),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    processed_at TIMESTAMP,
    status VARCHAR(30) DEFAULT 'RECEIVED' NOT NULL
);

-- Adapter command model for sending commands to devices
CREATE TABLE IF NOT EXISTS md_adapter_command (
    command_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    adapter_id UUID NOT NULL REFERENCES md_device_adapter(adapter_id) ON DELETE CASCADE,
    command_type VARCHAR(50) NOT NULL,
    command_payload JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(30) DEFAULT 'PENDING' NOT NULL,
    response_data JSONB NOT NULL DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    acknowledged_at TIMESTAMP
);

-- Adapter log model for tracking adapter activity
CREATE TABLE IF NOT EXISTS md_adapter_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    adapter_id UUID NOT NULL REFERENCES md_device_adapter(adapter_id) ON DELETE CASCADE,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    meta_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Device Adapter Indexes
CREATE INDEX idx_adapter_status ON md_device_adapter(status);
CREATE INDEX idx_adapter_type ON md_device_adapter(adapter_type);
CREATE INDEX idx_device_data_adapter_time ON md_device_data(adapter_id, received_at);
CREATE INDEX idx_device_data_patient_time ON md_device_data(patient_id, received_at);
CREATE INDEX idx_adapter_command_adapter ON md_adapter_command(adapter_id, status);
CREATE INDEX idx_adapter_log_adapter_time ON md_adapter_log(adapter_id, created_at);

-- ============================================================================
-- 5. CONFIG SERVICE TABLES (Config-as-Data)
-- ============================================================================

-- Config-as-data model for externalized configuration
CREATE TABLE IF NOT EXISTS md_config_item (
    config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(255) NOT NULL,
    config_value JSONB NOT NULL DEFAULT '{}',
    data_type VARCHAR(20) NOT NULL,
    scope VARCHAR(20) NOT NULL,
    scope_id UUID,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE NOT NULL,
    is_required BOOLEAN DEFAULT FALSE NOT NULL,
    default_value JSONB,
    validation_rules JSONB NOT NULL DEFAULT '{}',
    version INTEGER DEFAULT 1 NOT NULL,
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    effective_from TIMESTAMP,
    effective_to TIMESTAMP,
    UNIQUE(config_key, scope, scope_id)
);

-- Config history model for tracking configuration changes
CREATE TABLE IF NOT EXISTS md_config_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES md_config_item(config_id) ON DELETE CASCADE,
    config_key VARCHAR(255) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    change_reason TEXT,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    version INTEGER NOT NULL
);

-- Config group model for organizing related configuration items
CREATE TABLE IF NOT EXISTS md_config_group (
    group_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_name VARCHAR(255) UNIQUE NOT NULL,
    group_code VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    parent_group_id UUID REFERENCES md_config_group(group_id),
    sort_order INTEGER DEFAULT 0 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Config group mapping model
CREATE TABLE IF NOT EXISTS md_config_group_mapping (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES md_config_group(group_id) ON DELETE CASCADE,
    config_id UUID NOT NULL REFERENCES md_config_item(config_id) ON DELETE CASCADE,
    sort_order INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(group_id, config_id)
);

-- Config Service Indexes
CREATE INDEX idx_config_key_scope ON md_config_item(config_key, scope);
CREATE INDEX idx_config_category ON md_config_item(category);
CREATE INDEX idx_config_scope_id ON md_config_item(scope, scope_id);
CREATE INDEX idx_config_history_config_time ON md_config_history(config_id, changed_at);
CREATE INDEX idx_config_group_mapping ON md_config_group_mapping(group_id, config_id);

-- ============================================================================
-- 6. APPROVAL GATES TABLES
-- ============================================================================

-- Approval gate model for high-risk operations
CREATE TABLE IF NOT EXISTS md_approval_gate (
    gate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gate_name VARCHAR(255) NOT NULL,
    gate_code VARCHAR(100) UNIQUE NOT NULL,
    gate_type VARCHAR(50) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    description TEXT,
    approval_criteria JSONB NOT NULL DEFAULT '{}',
    required_roles JSONB NOT NULL DEFAULT '[]',
    auto_approve_after_minutes INTEGER,
    notify_approvers BOOLEAN DEFAULT TRUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    facility_id UUID REFERENCES md_facility(facility_id),
    specialty_profile_id UUID REFERENCES md_specialty_profile(specialty_profile_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Approval request model for tracking approval workflows
CREATE TABLE IF NOT EXISTS md_approval_request (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gate_id UUID NOT NULL REFERENCES md_approval_gate(gate_id) ON DELETE CASCADE,
    request_type VARCHAR(50) NOT NULL,
    request_data JSONB NOT NULL DEFAULT '{}',
    requester_id UUID NOT NULL,
    requester_name VARCHAR(255) NOT NULL,
    patient_id UUID REFERENCES md_patient(patient_id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES md_encounter(encounter_id) ON DELETE CASCADE,
    priority VARCHAR(20) DEFAULT 'MEDIUM' NOT NULL,
    status VARCHAR(30) DEFAULT 'PENDING' NOT NULL,
    urgency_reason TEXT,
    expires_at TIMESTAMP,
    approved_at TIMESTAMP,
    rejected_at TIMESTAMP,
    approved_by VARCHAR(100),
    rejected_by VARCHAR(100),
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Approval action model for tracking individual approval actions
CREATE TABLE IF NOT EXISTS md_approval_action (
    action_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES md_approval_request(request_id) ON DELETE CASCADE,
    approver_id UUID NOT NULL,
    approver_name VARCHAR(255) NOT NULL,
    approver_role VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,
    comments TEXT,
    action_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Approval Gates Indexes
CREATE INDEX idx_approval_request_status_priority ON md_approval_request(status, priority);
CREATE INDEX idx_approval_request_patient ON md_approval_request(patient_id, created_at);
CREATE INDEX idx_approval_action_request ON md_approval_action(request_id, created_at);

-- ============================================================================
-- 7. WEBHOOK PUBLISHER TABLES
-- ============================================================================

-- Webhook subscription model for external integrations
CREATE TABLE IF NOT EXISTS md_webhook_subscription (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_name VARCHAR(255) UNIQUE NOT NULL,
    subscriber_name VARCHAR(255) NOT NULL,
    webhook_url VARCHAR(500) NOT NULL,
    secret_key VARCHAR(255),
    event_types JSONB NOT NULL DEFAULT '[]',
    headers JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL,
    retry_policy JSONB NOT NULL DEFAULT '{}',
    timeout_seconds INTEGER DEFAULT 30 NOT NULL,
    verify_ssl BOOLEAN DEFAULT TRUE NOT NULL,
    filter_rules JSONB NOT NULL DEFAULT '{}',
    rate_limit_per_minute INTEGER DEFAULT 60 NOT NULL,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_triggered_at TIMESTAMP
);

-- Webhook delivery tracking model
CREATE TABLE IF NOT EXISTS md_webhook_delivery (
    delivery_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES md_webhook_subscription(subscription_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_id UUID,
    payload JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(30) DEFAULT 'PENDING' NOT NULL,
    http_status_code INTEGER,
    response_body TEXT,
    attempt_count INTEGER DEFAULT 0 NOT NULL,
    max_attempts INTEGER DEFAULT 3 NOT NULL,
    next_retry_at TIMESTAMP,
    error_message TEXT,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Webhook activity log model
CREATE TABLE IF NOT EXISTS md_webhook_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID REFERENCES md_webhook_subscription(subscription_id) ON DELETE CASCADE,
    delivery_id UUID REFERENCES md_webhook_delivery(delivery_id) ON DELETE CASCADE,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Webhook Publisher Indexes
CREATE INDEX idx_webhook_status ON md_webhook_subscription(status);
CREATE INDEX idx_webhook_event_types ON md_webhook_subscription(event_types);
CREATE INDEX idx_webhook_delivery_subscription ON md_webhook_delivery(subscription_id, created_at);
CREATE INDEX idx_webhook_delivery_status ON md_webhook_delivery(status, created_at);
CREATE INDEX idx_webhook_log_subscription_time ON md_webhook_log(subscription_id, created_at);

-- ============================================================================
-- 8. SUGGESTION TRACKER TABLES
-- ============================================================================

-- AI suggestion model for tracking AI-generated suggestions
CREATE TABLE IF NOT EXISTS md_suggestion (
    suggestion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    encounter_id UUID REFERENCES md_encounter(encounter_id) ON DELETE CASCADE,
    patient_id UUID REFERENCES md_patient(patient_id) ON DELETE CASCADE,
    suggestion_type VARCHAR(50) NOT NULL,
    suggestion_content JSONB NOT NULL,
    ai_model_version VARCHAR(50),
    confidence_score NUMERIC(5,4),
    context_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Suggestion feedback model for tracking clinician responses
CREATE TABLE IF NOT EXISTS md_suggestion_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    suggestion_id UUID NOT NULL REFERENCES md_suggestion(suggestion_id) ON DELETE CASCADE,
    acceptance_status VARCHAR(30) NOT NULL,
    rejection_reason VARCHAR(255),
    modified_content JSONB,
    feedback_from VARCHAR(100),
    time_to_decision_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Suggestion analytics model for tracking suggestion performance
CREATE TABLE IF NOT EXISTS md_suggestion_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    suggestion_type VARCHAR(50) NOT NULL,
    date_date DATE NOT NULL,
    total_suggestions INTEGER DEFAULT 0 NOT NULL,
    accepted_count INTEGER DEFAULT 0 NOT NULL,
    rejected_count INTEGER DEFAULT 0 NOT NULL,
    modified_count INTEGER DEFAULT 0 NOT NULL,
    average_confidence_score NUMERIC(5,4),
    average_time_to_decision_seconds NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(suggestion_type, date_date)
);

-- Suggestion pattern model for identifying patterns in suggestion acceptance
CREATE TABLE IF NOT EXISTS md_suggestion_pattern (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(50) NOT NULL,
    pattern_data JSONB NOT NULL DEFAULT '{}',
    frequency INTEGER DEFAULT 1 NOT NULL,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Suggestion Tracker Indexes
CREATE INDEX idx_suggestion_encounter ON md_suggestion(encounter_id);
CREATE INDEX idx_suggestion_type ON md_suggestion(suggestion_type);
CREATE INDEX idx_suggestion_feedback_acceptance ON md_suggestion_feedback(acceptance_status);
CREATE INDEX idx_suggestion_analytics_date ON md_suggestion_analytics(date_date);
CREATE INDEX idx_suggestion_pattern_type ON md_suggestion_pattern(pattern_type);

-- ============================================================================
-- 9. PROMPT MAPPINGS TABLES (Specialty UI)
-- ============================================================================

-- Prompt mapping model for mapping AI prompts to UI elements
CREATE TABLE IF NOT EXISTS md_prompt_mapping (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    specialty_profile_id UUID REFERENCES md_specialty_profile(specialty_profile_id),
    ui_element_id VARCHAR(255) NOT NULL,
    ui_element_type VARCHAR(50) NOT NULL,
    prompt_template TEXT NOT NULL,
    trigger_condition JSONB NOT NULL DEFAULT '{}',
    context_variables JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    sort_order INTEGER DEFAULT 0 NOT NULL,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Prompt variable model for reusable prompt variables
CREATE TABLE IF NOT EXISTS md_prompt_variable (
    variable_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variable_name VARCHAR(100) UNIQUE NOT NULL,
    variable_type VARCHAR(50) NOT NULL,
    default_value JSONB,
    description TEXT,
    category VARCHAR(50),
    is_system BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Prompt execution log for tracking prompt usage
CREATE TABLE IF NOT EXISTS md_prompt_execution (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mapping_id UUID REFERENCES md_prompt_mapping(mapping_id) ON DELETE CASCADE,
    encounter_id UUID REFERENCES md_encounter(encounter_id) ON DELETE CASCADE,
    patient_id UUID REFERENCES md_patient(patient_id) ON DELETE CASCADE,
    prompt_text TEXT NOT NULL,
    context_data JSONB NOT NULL DEFAULT '{}',
    ai_response TEXT,
    execution_time_ms NUMERIC(10,2),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Prompt Mappings Indexes
CREATE INDEX idx_prompt_mapping_specialty ON md_prompt_mapping(specialty_profile_id);
CREATE INDEX idx_prompt_mapping_element ON md_prompt_mapping(ui_element_id);
CREATE INDEX idx_prompt_execution_encounter ON md_prompt_execution(encounter_id);

-- ============================================================================
-- 10. DOCUMENT TEMPLATE MAPPINGS TABLES (Specialty UI)
-- ============================================================================

-- Document template mapping model
CREATE TABLE IF NOT EXISTS md_document_template_mapping (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    specialty_profile_id UUID REFERENCES md_specialty_profile(specialty_profile_id),
    document_type VARCHAR(50) NOT NULL,
    template_id VARCHAR(255) NOT NULL,
    template_name VARCHAR(255) NOT NULL,
    template_content TEXT NOT NULL,
    required_fields JSONB NOT NULL DEFAULT '[]',
    optional_fields JSONB NOT NULL DEFAULT '[]',
    validation_rules JSONB NOT NULL DEFAULT '{}',
    output_format VARCHAR(50) DEFAULT 'PDF',
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    version INTEGER DEFAULT 1 NOT NULL,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Document Template Mappings Indexes
CREATE INDEX idx_doc_template_specialty ON md_document_template_mapping(specialty_profile_id);
CREATE INDEX idx_doc_template_type ON md_document_template_mapping(document_type);

-- ============================================================================
-- 11. DOCTOR PREFERENCES TABLES (Specialty UI)
-- ============================================================================

-- Doctor preference model for personalized UI preferences
CREATE TABLE IF NOT EXISTS md_doctor_preference (
    preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinician_id UUID NOT NULL REFERENCES md_clinician(clinician_id) ON DELETE CASCADE,
    preference_key VARCHAR(100) NOT NULL,
    preference_value JSONB NOT NULL,
    preference_category VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(clinician_id, preference_key)
);

-- Doctor Preferences Indexes
CREATE INDEX idx_doctor_preference_clinician ON md_doctor_preference(clinician_id);
CREATE INDEX idx_doctor_preference_key ON md_doctor_preference(preference_key);
CREATE INDEX idx_doctor_preference_category ON md_doctor_preference(preference_category);

-- ============================================================================
-- COMMENTS
-- ============================================================================

-- This migration completes the implementation of all missing features
-- identified in the Health Platform Development Pack gap analysis.
-- 
-- After running this migration, the following features will be fully implemented:
-- - Event Bus (with webhook, service, and queue delivery)
-- - Longitudinal Record Index (with timeline and search cache)
-- - Clinical Rule Engine (with execution tracking and alerts)
-- - Device Adapter Framework (with data logging and command handling)
-- - Config-as-Data Service (with history and group management)
-- - Approval Gates (for high-risk operations)
-- - Webhook Publisher (for external integrations)
-- - Suggestion Tracker (for AI performance analytics)
-- - Prompt Mappings (for specialty-specific AI prompts)
-- - Document Template Mappings (for dynamic document generation)
-- - Doctor Preferences (for personalized clinician experience)
-- 
-- Next steps:
-- 1. Run this migration against your database
-- 2. Populate initial configuration data
-- 3. Create pre-built clinical rules
-- 4. Set up device adapters for your hardware
-- 5. Configure webhooks for external integrations
-- 6. Implement frontend components for new features
