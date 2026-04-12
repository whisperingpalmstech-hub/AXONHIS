# AXONHIS: Functional Requirements & Feature Specification (v1.0)

This document provides a comprehensive overview of all implemented features, engines, and modules within the **AXONHIS** (AI-First Hospital Information System) platform.

---

## 1. Core Platform & Enterprise Infrastructure (Phase 1)

### 1.1 Multi-Tenancy & Administration Engine
*   **Cross-Tenant Isolation**: Complete logical separation of data using `org_id` across all database models (Patients, Encounters, Billing, Wards).
*   **Organization Management**: Module for managing hospital branches, sub-organizations, and specific organizational settings.
*   **Role-Based Access Control (RBAC)**: Fine-grained permission system managing user access to specific clinical and administrative functions.

### 1.2 Enterprise Auth & Security Engine
*   **JWT-Based Authentication**: Secure stateless authentication for all API endpoints.
*   **Session Management**: Tracking of active user sessions with token invalidation capabilities.
*   **Security Headers & Middleware (Phase 11)**: HIPAA-compliant security headers and rate-limiting to prevent brute-force attacks.
*   **Audit Logging**: Comprehensive `AuditLog` system tracking all critical actions (Bed allocation, status changes, billing updates) including timestamp and user ID.

### 1.3 System Observability & Monitoring
*   **Centralized Health Monitoring**: Real-time health checks for DB, Redis, and Celery workers.
*   **System Error Logging**: Centralized logging of application errors for performance tuning and troubleshooting.
*   **Activity Dashboards**: High-level observability of system performance and process times.

---

## 2. Patient Lifecycle Management

### 2.1 Patient Registration & EMR
*   **Master Patient Index (MPI)**: Centralized patient database with unique UHIDs and UUIDs.
*   **Patient History**: Unified view of all patient encounters spanning OPD, IPD, and Lab.
*   **ABDM Integration**: Support for Indian ABHA (Ayushman Bharat Health Account) IDs and ABDM health record exchange protocols (Phase 1).

### 2.2 Patient Portal Engine (Phase 16)
*   **Web Portal**: Secure access for patients to view medical records, lab results, and upcoming appointments.
*   **Communication Engine**: Automated notifications (Email/SMS) for appointment reminders and critical result alerts.

---

## 3. Outpatient Department (OPD) Ecosystem

### 3.1 OPD Visit Intelligence Engine
*   **Visit Orchestration**: End-to-end management of OPD visits from appointment scheduling to final checkout.
*   **Walk-in Management**: Support for spontaneous patient visits and immediate triage.

### 3.2 Smart Queue & Flow Orchestration
*   **Live Queue Dashboards**: Real-time tracking of patient flows across departments.
*   **Wait-Time Estimation**: Analytical prediction of wait times to improve patient satisfaction.

### 3.3 Nursing Clinical Triage Engine
*   **Vital Recording**: Digitized entry for Blood Pressure, Pulse, SPO2, BMI, and Temp.
*   **Severity Scoring**: Initial clinical assessment and prioritization (Triage category assignment).

### 3.4 AI Doctor Desk & Intelligent EMR
*   **CPOE (Computerized Provider Order Entry)**: Electronic entry of lab orders, medications, and imaging requests.
*   **Clinical Notes (SOAP)**: Structured entry for Subjective, Objective, Assessment, and Plan notes.
*   **Medication Prescribing**: Database-linked prescription entry with dosage and frequency configuration.

---

## 4. Inpatient Department (IPD) Ecosystem

### 4.1 IPD Admission & Bed Management (Phase 10)
*   **Admission Request Workflow**: Request-to-Approval cycle for planned and emergency admissions.
*   **Bed Allocation Engine**: Visual ward-level bed management with real-time occupancy status (`available`, `occupied`, `cleaning`, `maintenance`).
*   **Ward Hierarchy**: Management of Wards, Rooms, and specific Bed categories (Standard, ICU, Isolation).

### 4.2 IPD Nursing Clinical Workspace (Phase 15)
*   **Nursing Worklist**: Real-time list of pending nursing tasks for admitted patients.
*   **Nursing Coversheet**: Specialized nursing view for vital monitoring and medication administration records.
*   **Patient Status Monitoring**: Real-time state tracking of admitted patients (Admitted, Pending Acceptance, Discharged).

### 4.3 Operating Theatre (OT) Management (Phase 14)
*   **Surgical Scheduling**: Workflow for booking OTs and coordinating surgical teams.
*   **Peri-operative Records**: Documentation management for pre-op, intra-op, and post-op surgical stages.

---

## 5. Diagnostics & Ancillary Services

### 5.1 LIS Laboratory Information System
*   **Test Order Management Engine**: Full lifecycle tracking of lab orders from OPD/IPD request to result entry.
*   **Phlebotomy Engine**: Tracking of specimen collection and barcode-aligned labeling.
*   **Analyzer Integration Engine**: Logic for receiving results directly from diagnostic machines.
*   **Result Validation & Approval**: Multi-tier validation workflow for lab technicians and pathologists.
*   **Reporting Engine**: Generation of patient-facing lab reports.

### 5.2 Radiology & Imaging Management (Phase 11)
*   **Imaging Workflow**: Request management for X-Rays, MRIs, and CT Scans.
*   **Radiology Reporting**: Templated reporting for radiologists.

### 5.3 Blood Bank Management (Phase 13)
*   **Inventory Control**: Real-time tracking of blood units by group and type.
*   **Cross-matching Workflow**: Safety check engine for blood transfusions.

---

## 6. Pharmacy & Medication Management

### 6.1 Pharmacy Sales & Inventory
*   **Sales Engine**: Point-of-Sale (POS) for walk-in and prescription-based drug sales.
*   **Real-time Stock Tracking**: Automatic deduction of inventory upon sale or clinical dispensing.
*   **Prescription Upload**: Feature for scanning and attaching physical prescriptions to digital sales records.

### 6.2 Dispensing Workflow
*   **Wait-list Management**: Automated queue for patients waiting for medication at the pharmacy counter.

---

## 7. Revenue Cycle Management (RCM) & Financials

### 7.1 Encounter Bridge Service (Phase 23)
*   **Cross-Module Financial Sync**: Automated engine that captures clinical actions (Lab orders, Pharmacy sales, IPD services) and pushes them to the billing module in real-time.

### 7.2 RCM Billing & Settlement Engine
*   **Claim Lifecycle Tracking**: Status tracking for insurance claims from submission to settlement.
*   **Payment Collection**: Support for multiple payment modes and receipt generation.
*   **Credit/Debit Management**: Handling of patient balances and credits.

### 7.3 Billing & Insurance
*   **Dynamic Itemization**: Support for diverse billing items (Doctor fees, Bed charges, Lab tests, Medication).
*   **Invoice Generation**: Detailed bill generation for OPD visits and IPD admissions.
*   **Discount & Authorization**: Multi-tier approval workflow for financial discounts.

---

## 8. AI & Advanced Intelligence

### 8.1 Clinical Decision Support (CDSS) (Phase 12)
*   **Condition Analysis**: AI-driven evaluation of vital signs and history to provide clinical suggestions.

### 8.2 Role-Based AI Assistant (Phase 26)
*   **Context-Aware Help**: Integrated AI agents (RPIW Assistant) that provide specialized help depending on the user's role (Doctor, Nurse, Administrator).

### 8.3 RPIW (Role-Based Patient Interaction Workspace) (Phase 23)
*   **Unified Summary Engine (Phase 24)**: AI-generated patient summaries and longitudinal health views.
*   **Clinical Action Engine (Phase 25)**: Accelerated workflows for clinical tasks directly from the unified workspace.

---

## 9. Analytics & Hospital Intelligence

### 9.1 Hospital Intelligence Dashboard
*   **Performance Metrics**: Tracking of departmental performance, patient throughput, and occupancy rates.
*   **Revenue Analytics**: High-level tracking of billables and revenue per department.
*   **Operational Health Monitoring**: Real-time status of system resources and hospital uptime.

---

## 10. Implemented Integration Architecture

| Service | Technology | Role |
| :--- | :--- | :--- |
| **Backend** | Python / FastAPI / SQLAlchemy | Enterprise Business Logic & REST API |
| **Frontend** | React / Next.js / Tailwind | Hospital Dashboard & Patient Portal |
| **Worker** | Celery / Redis | Async Analytics & Scheduled Health Checks |
| **Database** | PostgreSQL | Multi-tenant Relational storage |
| **Files** | Local / S3 Storage | Medical imaging and scanned documents storage |
