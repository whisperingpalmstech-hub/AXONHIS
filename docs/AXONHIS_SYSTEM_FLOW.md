# AXONHIS: Enterprise Hospital Information System
## Complete System Architecture & End-to-End Clinical Flow

AXONHIS is a state-of-the-art, AI-first Healthcare Information System designed to manage every aspect of a modern hospital's operations. The system is built on a highly scalable, microservices-oriented monolithic architecture using **FastAPI** (Python backend), **PostgreSQL** (relational database), **Redis** (caching and rate-limiting), and **Next.js** (React frontend).

This document outlines the entire flow of the system, covering all modules from patient registration to patient discharge, billing, and system administration.

---

## 1. Core Infrastructure & Security (The Foundation)
Before a user even interacts with clinical data, the core platform ensures security, traceability, and high availability.

### 1.1 Role-Based Access Control (RBAC) & Authentication (Phase 1)
*   **Authentication Flow**: Users (System Administrators, Doctors, Nurses, Pharmacists, Lab Technicians, Billing Staff) log in via JWT (JSON Web Tokens).
*   **Permissions**: Each user is assigned specific roles (e.g., `doctor`, `nurse`, `system_admin`). API endpoints are protected by a permissions engine. For instance, a nurse cannot approve a complex clinical order, and a doctor cannot access the underlying system server logs.
*   **Audit Logging**: Every sensitive action (creating a patient, editing a prescription, processing a payment) is strictly logged to an immutable `audit_logs` table for compliance (HIPAA).

### 1.2 System Administration & Reliability (Phase 11)
*   **Control Center**: Administrators have a dedicated dashboard to monitor real-time API latency, CPU/Memory usage, active database connections, and background job queues.
*   **Error Tracking**: Unhandled exceptions are automatically captured and cleanly presented in the monitoring dashboard, allowing engineers to squash bugs quickly.
*   **Disaster Recovery**: Automated Bash scripts run hourly and daily to take encrypted snapshot backups of the PostgreSQL database, storing them securely off-site to prevent data loss.

---

## 2. The Patient Journey: End-to-End Workflow
This section describes the practical workflow of a patient moving through the hospital, mapping real-world actions to AXONHIS modules.

### Step 1: Patient Arrival & Registration (Phase 2 - Patient Registry)
*   **Action**: A new patient walks into the hospital reception.
*   **System Event**: The receptionist searches the registry. If the patient is new, they capture:
    *   **Demographics**: Name, DOB, gender, address.
    *   **Identifiers**: National ID, Passport, or Internal Medical Record Number (MRN).
    *   **Emergency Contacts & Guardians**: Connected safely to the patient record.
    *   **Insurance Details**: Provider name, policy number, and coverage dates.
    *   **Consents**: Digital signing of privacy policies and treatment consents.

### Step 2: Triage & Encounter Creation (Phase 3 - Encounters)
*   **Action**: The patient is routed to a specific department (e.g., Cardiology, General Practice).
*   **System Event**: An **Encounter** is created. This encounter serves as the "wrapper" or "session" for everything that happens during this specific visit.
*   **Vitals Tracking**: Nurses log preliminary vitals (blood pressure, temperature, weight).

### Step 3: Physician Consultation & Notes (Phase 3 - Clinical Notes)
*   **Action**: The doctor sees the patient.
*   **System Event**:
    *   The doctor opens the active Encounter.
    *   **Clinical Notes**: The doctor writes SOAP (Subjective, Objective, Assessment, Plan) notes.
    *   **Diagnoses**: The doctor assigns standard diagnosis codes (ICD-10) to the patient encounter.
    *   **Clinical Flags**: If the patient has allergies or a high-risk condition, the doctor attaches a "Clinical Flag" which alerts all other staff interacting with this patient.

### Step 4: Orders & Clinical Workflows (Phases 4 & 5)
*   **Action**: The doctor determines the patient needs a blood test and some medication.
*   **System Event (Order Management)**: The doctor creates two clinical **Orders**:
    1.  A Laboratory Order for a Complete Blood Count (CBC).
    2.  A Pharmacy Order for prescribed antibiotics.
*   **System Event (Task Queue)**: Creating these orders automatically triggers actionable "Tasks" in the system queue:
    *   A task is routed to the Phlebotomist (Nurse) to collect the blood sample.
    *   A notification is dispatched to the Pharmacy to prepare the medication.

### Step 5: Departmental Execution – Laboratory (Phase 6)
*   **Action**: The patient goes to the lab for blood draw.
*   **System Event**:
    *   **Sample Collection**: The lab technician marks the sample as 'collected' in the Tasks dashboard.
    *   **Processing**: The sample moves to the backend lab machines.
    *   **Results & Validation**: Results are fed back into the Lab module. A senior pathologist reviews and "Validates" the results. If a result is critically high/low, AXONHIS triggers an immediate **Notification** to the ordering physician.

### Step 6: Departmental Execution – Pharmacy (Phase 7)
*   **Action**: The patient goes to the pharmacy to pick up medication.
*   **System Event**:
    *   **Prescription Queue**: The pharmacist sees the approved prescription.
    *   **Inventory check**: AXONHIS cross-references the required drug against live stock.
    *   **Batch Management**: The system deducts the stock from specific drug batches (tracking exact expiry dates). If aggregate stock falls below the threshold, a "Low Stock Alert" is triggered for procurement.
    *   **Dispensing**: The pharmacist hands over the drugs and marks the prescription as "Dispensed".

### Step 7: AI/ML Assistance (Phase 9 - AI Platform)
*   *Throughout the patient journey*, AXONHIS leverages an AI Inference Engine (Grok):
    *   **Transcription**: The doctor can use voice-to-text to dictate clinical notes seamlessly.
    *   **Predictive Analytics**: The AI analyzes the patient's vitals, lab results, and history to flag potential unobserved risks or suggest specific diagnostic paths.
    *   **Summary**: Upon discharge, the AI can synthesize a smart "Discharge Summary" from all the raw notes and lab data accumulated during the encounter.

### Step 8: Billing & Discharge (Phase 8 - Billing)
*   **Action**: The patient's visit concludes, and it is time to settle the financials.
*   **System Event**:
    *   AXONHIS's automated billing engine has been silently compiling charges based on the Encounter: The consultation fee, the lab test fee, and the pharmaceutical drug costs.
    *   **Invoice Generation**: A consolidated invoice is created.
    *   **Insurance Claims**: If the patient is insured, the system automatically splits the bill (Co-pay vs. Payer responsibility) and formats a claim for the insurance provider.
    *   **Payment Collection**: The cashier records the patient's out-of-pocket payment via credit card or cash, updating the invoice status to "Paid".
*   **Discharge**: The Encounter status is finally marked as "Completed / Discharged".

---

## 3. Hospital Administration (Phase 10 - Analytics)
While clinical staff deal with patients, Hospital Administrators use AXONHIS differently.
*   **Dashboards**: Administrators see macroscopic, top-down dashboards calculating revenue grouped by department, mapping the flow of peak patient times, and aggregating total outstanding invoices.
*   **Inventory Reports**: Identifying capital locked in near-expiry pharmacy inventory to inform stock liquidation or return strategies.

---

## Summary of Data Flow (Technical)
1. **Frontend Request**: The React UI calls a Next.js server action or fetches directly from the FastAPI backend.
2. **Gateway / Middleware**: The request hits FastAPI. Security headers are injected, rate limits (Redis) are verified, and JWT Auth is validated. Request timing begins.
3. **Controller/Router**: The request reaches the specific module (e.g., `app.core.encounters.routes`).
4. **Service Layer**: Business logic executes. e.g., "Can this prescription be dispensed?"
5. **Database Transaction**: SQLAlchemy processes a transactional query to PostgreSQL. If this transaction updates inventory, it's committed atomically. 
6. **Background Tasks**: If the action requires a heavy process (e.g., generating an AI summary, pushing a WebSocket notification), the task is handed off to Celery/Redis queues so the API responds instantly.
7. **Response to Client**: Data is serialized via Pydantic back to the frontend, which dynamically updates its state.

---
**AXONHIS ensures high-fidelity care execution while closing the loop on financial capture, inventory management, and system observability.**
