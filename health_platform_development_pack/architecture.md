
# Unified Clinical Practice + Health ATM Platform - Architecture Blueprint

## 1. Architectural goals
- one encounter engine across clinic, teleconsult, Health ATM, and hybrid care
- simple clinician experience
- specialty-specific experience packs
- longitudinal patient file
- patient-controlled sharing
- integration-first design
- future agentic operations readiness

## 2. Logical layers

### Experience Layer
- Clinician Workspace
- Front Desk Console
- Health ATM Console
- Patient App / Portal
- External Doctor Share Viewer

### Workflow Layer
- Scheduling Service
- Queue Service
- Encounter Service
- Orders / Prescribing Service
- Documentation Service
- Billing Trigger Service
- Consent & Sharing Service
- Longitudinal Record Index

### Intelligence Layer
- AI Orchestrator
- Specialty Prompt Packs
- Clinical Rule Engine
- Suggestion Acceptance Tracker

### Integration Layer
- Device Adapter Framework
- Streaming Gateway
- External Connector Framework
- FHIR/API Gateway
- Webhook Publisher
- Event Bus

### Governance Layer
- Identity & Access Management
- Audit Service
- Monitoring & Diagnostics
- Configuration Service
- Tenant / Environment Service

## 3. Deployment style
Recommended initial deployment:
- modular monolith or service-oriented backend with clear domain boundaries
- PostgreSQL as primary transactional store
- object storage for documents, images, waveforms, and raw device outputs
- search index for fast retrieval across longitudinal record
- event broker for operational events and future automation hooks
- API gateway for internal and external access

## 4. Specialty UI strategy
Use a shared component library plus metadata-driven layouts:
- specialty profiles
- widget sets
- layout rules
- prompt mappings
- document template mappings
- limited doctor-level preferences

## 5. Integration strategy
- first-class internal APIs between modules
- external REST APIs
- FHIR-aligned mapping model
- adapter framework for external PMS/HIS/LIS/RIS systems
- event-driven notifications for operational workflows

## 6. Future autonomy hooks
Required from day one:
- structured logs
- correlation IDs
- operational event stream
- config-as-data
- machine-readable health endpoints
- human approval gates for high-risk operations
