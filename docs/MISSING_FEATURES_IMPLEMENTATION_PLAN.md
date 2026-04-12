# AxonHIS MD - Missing Features Implementation Plan

## Overview
This document provides detailed implementation specifications for all missing features identified in the comprehensive analysis against the Health Platform Development Pack.

**Current Implementation Coverage: ~70%**

---

## 🎯 CRITICAL PRIORITY (P0)

### 1. Longitudinal Record Index
**Module:** Workflow Layer  
**Purpose:** Fast retrieval across patient history  
**Impact:** Essential for clinical decision-making and patient care continuity

#### Technical Specification
- **Database Schema:** New table `longitudinal_record_index`
- **Search Engine:** Elasticsearch or PostgreSQL full-text search
- **Indexing Strategy:** Real-time indexing on encounter completion
- **Query Performance:** Sub-second response for patient timeline queries

#### Implementation Steps

**1.1 Database Schema**
```sql
create table longitudinal_record_index (
    index_id uuid primary key default uuid_generate_v4(),
    patient_id uuid not null references patient(patient_id) on delete cascade,
    encounter_id uuid references encounter(encounter_id),
    resource_type varchar(50) not null,
    resource_id varchar(255) not null,
    resource_summary text,
    clinical_date timestamptz not null,
    clinical_category varchar(50),
    tags jsonb not null default '{}'::jsonb,
    searchable_text text,
    indexed_at timestamptz not null default now()
);

create index idx_longitudinal_patient on longitudinal_record_index(patient_id, clinical_date desc);
create index idx_longitudinal_search on longitudinal_record_index using gin(searchable_text gin_trgm_ops);
create index idx_longitudinal_category on longitudinal_record_index(clinical_category);
```

**1.2 Backend Implementation**
- Create module: `backend/app/core/longitudinal/`
- Implement indexer service that triggers on:
  - Encounter completion
  - Diagnosis creation
  - Service request creation
  - Document upload
  - Medication request
- Implement search API:
  - `/api/v1/longitudinal/patients/{patientId}/timeline`
  - `/api/v1/longitudinal/patients/{patientId}/search`
  - `/api/v1/longitudinal/patients/{patientId}/category/{category}`

**1.3 Frontend Integration**
- Create component: `frontend/src/components/longitudinal/PatientTimeline.tsx`
- Implement timeline visualization with filters
- Add search functionality across patient history
- Integrate with patient portal for patient view

**1.4 Dependencies**
- PostgreSQL with pg_trgm extension for text search
- OR Elasticsearch for advanced search (optional)
- Redis for caching frequent queries

**Estimated Effort:** 5-7 days

---

### 2. Event Bus
**Module:** Integration Layer  
**Purpose:** Enable event-driven architecture for automation  
**Impact:** Required for automation, integration, and real-time workflows

#### Technical Specification
- **Message Broker:** Redis Streams or RabbitMQ
- **Event Schema:** Standardized event format
- **Event Types:** 20+ clinical and operational events
- **Delivery Guarantees:** At-least-once delivery
- **Dead Letter Queue:** For failed events

#### Implementation Steps

**2.1 Database Schema**
```sql
create table event_bus (
    event_id uuid primary key default uuid_generate_v4(),
    event_type varchar(100) not null,
    event_version varchar(20) not null default '1.0',
    source_service varchar(100) not null,
    correlation_id varchar(100) not null,
    causation_id varchar(100),
    payload_json jsonb not null,
    event_status varchar(30) not null default 'PENDING',
    published_at timestamptz,
    processed_at timestamptz,
    error_message text,
    retry_count integer not null default 0,
    created_at timestamptz not null default now()
);

create table event_subscription (
    subscription_id uuid primary key default uuid_generate_v4(),
    event_type_pattern varchar(100) not null,
    subscriber_service varchar(100) not null,
    endpoint_url text,
    active_flag boolean not null default true,
    filter_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index idx_event_bus_status on event_bus(event_status, created_at desc);
create index idx_event_bus_correlation on event_bus(correlation_id);
create index idx_event_bus_type on event_bus(event_type);
```

**2.2 Backend Implementation**
- Create module: `backend/app/core/event_bus/`
- Implement event publisher:
  - `EventPublisher` class with publish methods
  - Integration with Redis Streams/RabbitMQ
  - Retry logic with exponential backoff
- Implement event subscriber:
  - `EventSubscriber` class for consuming events
  - Webhook delivery for external subscribers
  - DLQ handling
- Define event types:
  - `encounter.started`, `encounter.completed`
  - `diagnosis.created`, `diagnosis.updated`
  - `service_request.ordered`, `service_request.completed`
  - `medication.prescribed`
  - `document.uploaded`
  - `share_grant.created`, `share_grant.accessed`
  - `appointment.booked`, `appointment.cancelled`
  - `patient.registered`, `patient.updated`

**2.3 Event Registry**
- Create `backend/app/core/event_bus/events.py` with event schemas
- Implement event validation using Pydantic
- Version event schemas for backward compatibility

**2.4 Integration Points**
- Modify existing services to publish events:
  - Encounters module → encounter events
  - Orders module → service request events
  - Files module → document events
  - Patients module → patient and share events
  - Scheduling module → appointment events

**2.5 Dependencies**
- Redis (for streams) or RabbitMQ
- Python: `redis` or `pika` library
- Circuit breaker pattern for resilience

**Estimated Effort:** 7-10 days

---

### 3. Clinical Rule Engine
**Module:** Intelligence Layer  
**Purpose:** Clinical decision support beyond AI  
**Impact:** Patient safety, guideline compliance, quality care

#### Technical Specification
- **Rule Format:** JSON-based rule definitions
- **Rule Types:** Validation, alerting, recommendation
- **Execution Engine:** Rule-based inference
- **Context:** Patient data, encounter data, specialty context
- **Action Types:** Block, warn, suggest, auto-fill

#### Implementation Steps

**3.1 Database Schema**
```sql
create table clinical_rule (
    rule_id uuid primary key default uuid_generate_v4(),
    rule_code varchar(100) unique not null,
    rule_name varchar(255) not null,
    rule_category varchar(50) not null,
    rule_type varchar(30) not null,
    specialty_profile_id uuid references specialty_profile(specialty_profile_id),
    rule_definition jsonb not null,
    severity_level varchar(30) not null default 'INFO',
    active_flag boolean not null default true,
    version_no integer not null default 1,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table clinical_rule_execution (
    execution_id uuid primary key default uuid_generate_v4(),
    rule_id uuid not null references clinical_rule(rule_id),
    encounter_id uuid references encounter(encounter_id),
    patient_id uuid references patient(patient_id),
    execution_context jsonb not null,
    trigger_type varchar(50) not null,
    action_taken varchar(50),
    action_result jsonb,
    executed_at timestamptz not null default now()
);

create index idx_clinical_rule_active on clinical_rule(active_flag, specialty_profile_id);
create index idx_rule_execution_encounter on clinical_rule_execution(encounter_id);
```

**3.2 Rule Definition Schema**
```json
{
  "rule_code": "DRUG_INTERACTION_CHECK",
  "rule_name": "Drug Interaction Check",
  "rule_category": "SAFETY",
  "rule_type": "VALIDATION",
  "trigger": {
    "event": "medication_request.created"
  },
  "conditions": {
    "all": [
      {
        "field": "medication_code",
        "operator": "in_interaction_group",
        "value": "existing_medications"
      }
    ]
  },
  "actions": [
    {
      "type": "BLOCK",
      "message": "Potential drug interaction detected",
      "severity": "HIGH"
    }
  ]
}
```

**3.3 Backend Implementation**
- Create module: `backend/app/core/clinical_rules/`
- Implement rule engine:
  - `RuleEngine` class for rule execution
  - `RuleParser` for parsing rule definitions
  - `RuleExecutor` for evaluating conditions
  - `ActionHandler` for executing actions
- Implement rule registry:
  - Load rules from database
  - Cache active rules in Redis
- Implement trigger handlers:
  - Medication request → drug interaction rules
  - Diagnosis → guideline compliance rules
  - Service request → appropriateness rules
  - Patient age → pediatric/geriatric rules

**3.4 Pre-built Rules**
- Drug-drug interaction checking
- Drug-allergy checking
- Age-appropriate dosing
- Duplicate test ordering
- Required documentation for procedures
- Billing code validation
- Specialty-specific guidelines (ICD-10, clinical pathways)

**3.5 Frontend Integration**
- Create component: `frontend/src/components/clinical_rules/RuleAlert.tsx`
- Display rule alerts in clinician workspace
- Allow clinicians to override with reason
- Track rule acceptance/rejection

**3.6 Dependencies**
- Python: `jsonschema` for rule validation
- Redis for rule caching
- External drug database (e.g., RxNorm) for interactions

**Estimated Effort:** 10-14 days

---

### 4. Device Adapter Framework
**Module:** Integration Layer  
**Purpose:** Device integration for Health ATM and clinical devices  
**Impact:** Essential for Health ATM functionality and vital sign capture

#### Technical Specification
- **Adapter Pattern:** Pluggable device adapters
- **Communication Protocols:** HL7, DICOM, Bluetooth, USB, REST
- **Device Types:** BP monitor, ECG, thermometer, pulse oximeter, glucometer
- **Data Flow:** Device → Adapter → Standardized format → Database
- **Error Handling:** Device disconnection, data validation

#### Implementation Steps

**4.1 Database Schema**
```sql
create table device_adapter (
    adapter_id uuid primary key default uuid_generate_v4(),
    adapter_code varchar(100) unique not null,
    adapter_name varchar(255) not null,
    device_class varchar(50) not null,
    protocol_type varchar(50) not null,
    adapter_config_json jsonb not null,
    active_flag boolean not null default true,
    created_at timestamptz not null default now()
);

create table device_session (
    session_id uuid primary key default uuid_generate_v4(),
    device_id uuid not null references device(device_id),
    encounter_id uuid references encounter(encounter_id),
    operator_user_ref varchar(100),
    session_status varchar(30) not null default 'ACTIVE',
    started_at timestamptz not null default now(),
    ended_at timestamptz
);

alter table device_result add column adapter_id uuid references device_adapter(adapter_id);
alter table device_result add column session_id uuid references device_session(session_id);
```

**4.2 Backend Implementation**
- Create module: `backend/app/core/device_adapters/`
- Implement adapter base class:
  ```python
  class DeviceAdapter(ABC):
      @abstractmethod
      async def connect(self, config: dict) -> bool:
          pass
      
      @abstractmethod
      async def disconnect(self) -> bool:
          pass
      
      @abstractmethod
      async def read_data(self) -> DeviceReading:
          pass
      
      @abstractmethod
      def normalize_data(self, raw_data: dict) -> dict:
          pass
  ```
- Implement specific adapters:
  - `BluetoothAdapter` for BLE devices
  - `HL7Adapter` for HL7 messages
  - `DICOMAdapter` for medical imaging
  - `RESTAdapter` for REST APIs
  - `USBAdapter` for USB devices
- Implement device manager:
  - Device discovery and pairing
  - Session management
  - Data streaming and buffering
  - Error handling and reconnection

**4.3 Standardized Data Format**
```json
{
  "device_code": "BP_MONITOR_001",
  "device_class": "BLOOD_PRESSURE",
  "timestamp": "2026-04-08T14:30:00Z",
  "readings": [
    {
      "observation_code": "SYSTOLIC_BP",
      "value": 120,
      "unit": "mmHg"
    },
    {
      "observation_code": "DIASTOLIC_BP",
      "value": 80,
      "unit": "mmHg"
    },
    {
      "observation_code": "PULSE",
      "value": 72,
      "unit": "bpm"
    }
  ],
  "metadata": {
    "device_serial": "SN12345",
    "firmware_version": "2.1.0"
  }
}
```

**4.4 Frontend Integration**
- Create component: `frontend/src/components/devices/DeviceManager.tsx`
- Health ATM console device connection UI
- Real-time vital sign display
- Device status monitoring

**4.5 Dependencies**
- Python: `bleak` for Bluetooth, `pydicom` for DICOM
- Hardware testing with actual devices
- Device simulators for development

**Estimated Effort:** 14-21 days

---

## 🔴 HIGH PRIORITY (P1)

### 5. Suggestion Acceptance Tracker
**Module:** Intelligence Layer  
**Purpose:** Track AI suggestion acceptance/rejection for learning  
**Impact:** AI model improvement, clinical insight, quality metrics

#### Technical Specification
- **Tracking Scope:** All AI-generated suggestions
- **Suggestion Types:** Diagnosis, treatment, documentation, coding
- **Metrics:** Acceptance rate, rejection reasons, time to decision
- **Feedback Loop:** Data for model fine-tuning

#### Implementation Steps

**5.1 Database Schema**
```sql
create table ai_suggestion (
    suggestion_id uuid primary key default uuid_generate_v4(),
    encounter_id uuid references encounter(encounter_id),
    patient_id uuid references patient(patient_id),
    suggestion_type varchar(50) not null,
    suggestion_content jsonb not null,
    ai_model_version varchar(50),
    confidence_score numeric(5,4),
    context_json jsonb not null,
    created_at timestamptz not null default now()
);

create table ai_suggestion_feedback (
    feedback_id uuid primary key default uuid_generate_v4(),
    suggestion_id uuid not null references ai_suggestion(suggestion_id),
    acceptance_status varchar(30) not null,
    rejection_reason varchar(255),
    modified_content jsonb,
    feedback_from varchar(100),
    time_to_decision_seconds integer,
    created_at timestamptz not null default now()
);

create index idx_ai_suggestion_encounter on ai_suggestion(encounter_id);
create index idx_ai_suggestion_type on ai_suggestion(suggestion_type);
create index idx_ai_feedback_acceptance on ai_suggestion_feedback(acceptance_status);
```

**5.2 Backend Implementation**
- Create module: `backend/app/core/ai_feedback/`
- Implement suggestion tracker:
  - `SuggestionTracker` class for logging suggestions
  - `FeedbackCollector` for capturing clinician decisions
  - `MetricsCalculator` for computing acceptance rates
- Integrate with AI module:
  - Wrap AI calls to log suggestions
  - Add feedback UI hooks
- Implement analytics endpoints:
  - `/api/v1/ai/suggestions/metrics`
  - `/api/v1/ai/suggestions/by-type/{type}`
  - `/api/v1/ai/suggestions/trends`

**5.3 Frontend Integration**
- Add feedback UI to all AI suggestion displays
- Quick accept/reject buttons
- Optional reason capture for rejection
- Modified content capture for partial acceptance

**5.4 Analytics Dashboard**
- Create dashboard for AI performance metrics
- Acceptance rate by suggestion type
- Top rejection reasons
- Model performance trends

**Estimated Effort:** 5-7 days

---

### 6. Webhook Publisher
**Module:** Integration Layer  
**Purpose:** External notifications for third-party integrations  
**Impact:** Enables real-time integrations with external systems

#### Technical Specification
- **Webhook Types:** Clinical events, operational events
- **Delivery:** Retry logic with exponential backoff
- **Security:** HMAC signature verification
- **Webhook Management:** CRUD operations for webhook subscriptions

#### Implementation Steps

**6.1 Database Schema**
```sql
create table webhook_subscription (
    subscription_id uuid primary key default uuid_generate_v4(),
    organization_id uuid references organization(organization_id),
    webhook_name varchar(255) not null,
    webhook_url text not null,
    event_types jsonb not null,
    secret_key varchar(255),
    active_flag boolean not null default true,
    retry_policy_json jsonb not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table webhook_delivery_log (
    delivery_id uuid primary key default uuid_generate_v4(),
    subscription_id uuid not null references webhook_subscription(subscription_id),
    event_id uuid not null,
    event_type varchar(100) not null,
    payload_json jsonb not null,
    http_status_code integer,
    response_body text,
    delivery_status varchar(30) not null,
    attempt_count integer not null default 1,
    next_retry_at timestamptz,
    delivered_at timestamptz,
    created_at timestamptz not null default now()
);

create index idx_webhook_active on webhook_subscription(active_flag, organization_id);
create index idx_webhook_delivery_status on webhook_delivery_log(delivery_status, next_retry_at);
```

**6.2 Backend Implementation**
- Create module: `backend/app/core/webhooks/`
- Implement webhook publisher:
  - `WebhookPublisher` class for delivering webhooks
  - Signature generation using HMAC-SHA256
  - Retry logic with exponential backoff
- Implement webhook manager:
  - CRUD API for webhook subscriptions
  - Webhook testing endpoint
  - Delivery log viewing
- Integrate with Event Bus:
  - Subscribe to relevant events
  - Publish to configured webhooks

**6.3 Webhook Payload Format**
```json
{
  "event_id": "uuid",
  "event_type": "encounter.completed",
  "timestamp": "2026-04-08T14:30:00Z",
  "data": {
    "encounter_id": "uuid",
    "patient_id": "uuid",
    "clinician_id": "uuid",
    "encounter_mode": "IN_PERSON",
    "encounter_status": "COMPLETED"
  },
  "signature": "hmac_signature"
}
```

**6.4 Dependencies**
- Python: `httpx` for async HTTP requests
- Redis for queue management
- Circuit breaker for resilience

**Estimated Effort:** 5-7 days

---

### 7. Streaming Gateway
**Module:** Integration Layer  
**Purpose:** Real-time data streaming for live monitoring  
**Impact:** Required for real-time vital sign monitoring, telemedicine

#### Technical Specification
- **Protocol:** WebSocket for real-time communication
- **Data Types:** Vital signs, device readings, chat messages
- **Scaling:** Horizontal scaling with Redis pub/sub
- **Authentication:** Token-based authentication

#### Implementation Steps

**7.1 Backend Implementation**
- Create module: `backend/app/core/streaming/`
- Implement WebSocket server:
  - Connection management
  - Room/channel management
  - Message routing
  - Authentication middleware
- Implement streaming endpoints:
  - `/ws/vital-signs/{encounterId}`
  - `/ws/chat/{encounterId}`
  - `/ws/device/{deviceId}`
- Integrate with Redis pub/sub for scaling

**7.2 Message Format**
```json
{
  "message_type": "vital_sign_update",
  "timestamp": "2026-04-08T14:30:00Z",
  "data": {
    "encounter_id": "uuid",
    "readings": [
      {
        "code": "HEART_RATE",
        "value": 72,
        "unit": "bpm"
      }
    ]
  }
}
```

**7.3 Frontend Integration**
- Create WebSocket client utilities
- Real-time vital sign charts
- Live chat for telemedicine
- Device streaming display

**7.4 Dependencies**
- Python: `fastapi-websocket-pubsub` or custom implementation
- Redis for pub/sub
- Frontend: WebSocket client libraries

**Estimated Effort:** 7-10 days

---

### 8. External Doctor Share Viewer
**Module:** Experience Layer  
**Purpose:** Allow external doctors to view shared patient records  
**Impact:** Enables patient-controlled sharing for second opinions

#### Technical Specification
- **Access Control:** Token-based, time-limited access
- **Scope Control:** Patient-defined share scope (summary vs full)
- **Audit Trail:** Complete access logging
- **Responsive Design:** Mobile-friendly for external access

#### Implementation Steps

**8.1 Database Schema**
```sql
-- Extend existing share_grant table with additional fields if needed
-- share_access_log table already exists for audit
```

**8.2 Backend Implementation**
- Create module: `backend/app/core/share_viewer/`
- Implement share viewer API:
  - `GET /api/v1/share/verify/{token}` - Verify share token
  - `GET /api/v1/share/patient/{token}` - Get patient summary
  - `GET /api/v1/share/encounters/{token}` - Get encounter history
  - `GET /api/v1/share/documents/{token}` - Get shared documents
- Implement scope enforcement:
  - Check share_grant scope_json
  - Filter data based on scope (summary vs full)
  - Respect sensitive category rules
- Implement access logging:
  - Log all access attempts
  - Track view duration
  - Record download actions

**8.3 Frontend Implementation**
- Create standalone viewer app: `apps/share-viewer/`
- Simple, clean UI optimized for external doctors
- Patient summary view
- Encounter timeline
- Document viewer
- No editing capabilities (read-only)

**8.4 Security**
- JWT tokens with expiration
- One-time use tokens for sensitive data
- Rate limiting
- IP whitelisting (optional)

**Estimated Effort:** 7-10 days

---

## 🟡 MEDIUM PRIORITY (P2)

### 9. Future Autonomy Hooks

#### 9.1 Structured Logs
**Purpose:** Machine-readable logs for automated analysis  
**Implementation:**
- Replace print statements with structured logging
- Use JSON format with correlation IDs
- Include context: user_id, tenant_id, request_id
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

**Library:** Python `structlog` or custom JSON formatter  
**Estimated Effort:** 3-5 days

#### 9.2 Correlation IDs
**Purpose:** Request tracing across services  
**Implementation:**
- Generate correlation ID on incoming requests
- Pass through all service calls
- Include in all logs and events
- Store in database for traceability

**Middleware:** FastAPI middleware for correlation ID injection  
**Estimated Effort:** 2-3 days

#### 9.3 Operational Event Stream
**Purpose:** Event streaming for automation  
**Implementation:**
- Already covered by Event Bus (P0)
- Additional: Event replay capability
- Event archival for analytics

**Estimated Effort:** 3-5 days (after Event Bus)

#### 9.4 Config-as-Data
**Purpose:** Externalized configuration for dynamic updates  
**Implementation:**
```sql
create table configuration (
    config_id uuid primary key default uuid_generate_v4(),
    config_key varchar(255) unique not null,
    config_value jsonb not null,
    config_type varchar(50) not null,
    environment varchar(50) not null,
    tenant_id uuid references organization(organization_id),
    active_flag boolean not null default true,
    version_no integer not null default 1,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
```
- Configuration API for CRUD operations
- Caching layer with Redis
- Configuration change events

**Estimated Effort:** 4-6 days

#### 9.5 Machine-Readable Health Endpoints
**Purpose:** Automated health checks for monitoring  
**Implementation:**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "checks": {
            "database": "healthy",
            "redis": "healthy",
            "event_bus": "healthy"
        }
    }

@app.get("/health/ready")
async def readiness_check():
    # Check if service can accept traffic
    pass

@app.get("/health/live")
async def liveness_check():
    # Check if service is running
    pass
```

**Estimated Effort:** 2-3 days

#### 9.6 Human Approval Gates
**Purpose:** Require approval for high-risk operations  
**Implementation:**
```sql
create table approval_request (
    request_id uuid primary key default uuid_generate_v4(),
    request_type varchar(100) not null,
    requested_by varchar(100) not null,
    request_payload jsonb not null,
    risk_level varchar(30) not null,
    status varchar(30) not null default 'PENDING',
    approved_by varchar(100),
    approved_at timestamptz,
    rejection_reason text,
    expires_at timestamptz,
    created_at timestamptz not null default now()
);
```
- Approval workflow service
- Approval UI for administrators
- Integration with high-risk operations

**Estimated Effort:** 5-7 days

---

### 10. Specialty UI Enhancements

#### 10.1 Prompt Mappings
**Purpose:** Map AI prompts to UI elements  
**Implementation:**
- Extend `specialty_profile.ui_config_json` with prompt mappings
- Define prompt triggers based on UI interactions
- Context-aware prompt generation

**Estimated Effort:** 3-4 days

#### 10.2 Document Template Mappings
**Purpose:** Map document templates to document types  
**Implementation:**
- Extend `specialty_profile.document_template_json`
- Template engine integration
- Dynamic document generation

**Estimated Effort:** 4-5 days

#### 10.3 Doctor-Level Preferences
**Purpose:** Personalized UI preferences per doctor  
**Implementation:**
```sql
create table clinician_preferences (
    preference_id uuid primary key default uuid_generate_v4(),
    clinician_id uuid not null references clinician(clinician_id),
    preference_key varchar(100) not null,
    preference_value jsonb not null,
    updated_at timestamptz not null default now(),
    unique (clinician_id, preference_key)
);
```
- Preferences API
- UI for managing preferences
- Preference application in frontend

**Estimated Effort:** 3-4 days

---

## 📊 IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Weeks 1-4)
**Priority:** P0 features  
**Features:**
1. Event Bus (Weeks 1-2)
2. Structured Logs & Correlation IDs (Week 3)
3. Machine-Readable Health Endpoints (Week 3)
4. Config-as-Data (Week 4)

**Deliverables:**
- Event-driven architecture foundation
- Observability improvements
- Dynamic configuration capability

### Phase 2: Clinical Intelligence (Weeks 5-8)
**Priority:** P0 + P1 features  
**Features:**
1. Longitudinal Record Index (Weeks 5-6)
2. Clinical Rule Engine (Weeks 6-8)
3. Suggestion Acceptance Tracker (Week 7)

**Deliverables:**
- Patient timeline view
- Clinical decision support
- AI performance tracking

### Phase 3: Integration & Devices (Weeks 9-12)
**Priority:** P0 + P1 features  
**Features:**
1. Device Adapter Framework (Weeks 9-11)
2. Webhook Publisher (Week 11)
3. Streaming Gateway (Week 12)

**Deliverables:**
- Health ATM device integration
- External system notifications
- Real-time data streaming

### Phase 4: Experience & Autonomy (Weeks 13-16)
**Priority:** P1 + P2 features  
**Features:**
1. External Doctor Share Viewer (Weeks 13-14)
2. Operational Event Stream (Week 14)
3. Human Approval Gates (Week 15)
4. Specialty UI Enhancements (Week 16)

**Deliverables:**
- Patient sharing capability
- Automation readiness
- Personalized clinician experience

---

## 🎯 SUCCESS METRICS

### Technical Metrics
- **Event Bus:** <100ms event publishing, 99.9% delivery rate
- **Longitudinal Index:** <500ms query response for 5-year history
- **Rule Engine:** <200ms rule evaluation, 0 false positives
- **Device Adapters:** 99% device connection success rate
- **Webhook Publisher:** 95% first-attempt delivery, 99% eventual delivery

### Clinical Metrics
- **Rule Engine:** 90% clinician acceptance of rule alerts
- **AI Tracker:** 60% suggestion acceptance rate baseline
- **Longitudinal Index:** 50% reduction in time to find patient history

### Integration Metrics
- **Device Adapters:** Support for 5+ device classes
- **Webhook Publisher:** 10+ external integrations
- **Streaming Gateway:** <100ms latency for vital sign updates

---

## 📝 NOTES

### Dependencies
- **PostgreSQL:** Required for all new schemas
- **Redis:** Required for Event Bus, caching, streaming
- **Elasticsearch:** Optional for advanced search (can use PostgreSQL)
- **Message Broker:** Redis Streams or RabbitMQ for Event Bus

### Risk Mitigation
- **Event Bus:** Implement DLQ and monitoring to prevent data loss
- **Rule Engine:** Start with read-only mode, enable blocking after validation
- **Device Adapters:** Extensive testing with actual devices required
- **Webhook Publisher:** Implement rate limiting to prevent abuse

### Testing Strategy
- Unit tests for all new modules
- Integration tests for event flows
- Load testing for Event Bus and Longitudinal Index
- Device testing with simulators and real devices
- Security testing for Webhook Publisher and Share Viewer

### Documentation Requirements
- API documentation for all new endpoints
- Event schema documentation
- Rule definition guide
- Device adapter development guide
- Webhook integration guide

---

## 🔗 RELATED DOCUMENTS

- [Health Platform Development Pack](../health_platform_development_pack/)
- [AxonHIS Architecture](./AXONHIS_SYSTEM_FLOW.md)
- [Clinical Workflow Testing](./CLINICAL_WORKFLOW_TESTING.md)
- [Database Schema](../health_platform_development_pack/db_schema.sql)
- [API Specification](../health_platform_development_pack/api_starter_spec.yaml)
