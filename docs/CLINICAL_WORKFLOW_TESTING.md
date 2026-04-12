# AXONHIS Clinical Workflow Integration & Testing Guide

This guide details the end-to-end integration architecture for the AXONHIS hospital platform. It provides testing instructions, expected output, and sample test data for validating the complete patient lifecycle, from entry to discharge.

---

## 1. Full Patient Journey Architecture

A patient's journey through AXONHIS touches multiple isolated modules that act as a single cohesive unit:

1. **System Initialization (Admin)**
   - Admin provisions the infrastructure: Users (roles), Wards/Beds, LIS Analyzers, Pharmacy Inventory, and Setup Tariffs.
2. **Patient Entry (Receptionist)**
   - The Front Office logs a new `Patient` resulting in a unique `UHID`.
   - An `Encounter` is spun up serving as the clinical session wrapper (OPD, Emergency, IPD).
3. **Nursing & Triage (Nursing Module / OPD)**
   - Vitals (BP, HR, SpO2) are captured and pinned to the Encounter.
   - The Triage Engine stratifies the priority.
4. **Clinical Assesment (Doctor Desk)**
   - Doctor opens the Encounter from the Queue.
   - Doctor issues Clinical Orders (Lab tests, Imaging, Medications) or decides for Admission.
5. **Department Execution**
   - **Laboratory (LIS):** Lab Order translates to a Phlebotomy task → LIS Sample Received → Analyzer Processing -> Validation → Results posted to Patient Workspace.
   - **Pharmacy:** Rx triggers Worklist → Pharmacist Verification → Stock allocation & Inventory deduction → Dispatch.
6. **Inpatient Handling (IPD / OT / Blood Bank)**
   - **IPD:** Doctor creates Admission Request → Bed Allocated → Nursing tasks (Medication Administration, Monitor) → Doctor Rounds.
   - **OT:** Procedure scheduled → Pre-op checklists → Surgery execution → Post-op recovery notes.
7. **Billing & RCM**
   - All modules (Labs, Medications, Interventions, Bed charges) automatically emit actionable billing segments.
   - RCM aggregates these into a final `Invoice`.
8. **Discharge & DocGen**
   - Clinical Discharge checks for unfulfilled lab/med orders.
   - Final Invoice generated. System compiles the `Discharge Summary` and generates PDFs.

---

## 2. Module Integration Event Flow

Every module communicates by updating states and referencing the core `Encounter ID` and `Patient ID`.

- **Doctor → LIS:** The creation of an `Order` of type `LAB` inserts a placeholder record in the LIS schema.
- **LIS → Doctor:** When the Pathologist updates the Lab Result state to `VALIDATED`, a notification payload is returned, and data is synced to the Patient Workspace `Labs` tab.
- **Doctor → Pharmacy:** Creating a `Prescription` directly updates the Pharmacy Rx Worklist queue.
- **Pharmacy → Billing:** The event `PRESCRIPTION_DISPENSED` initiates a ledger entry deducting `Inventory` and creating an `unbilled charge` mapped to the Encounter.
- **Doctor → IPD:** Admission recommendation inserts a record into `IpdAdmissionRequest` which alerts the Ward Management team.

---

## 3. Testing Steps & Sample Data

### Test Case 1: Patient Onboarding
*   **Role:** Receptionist
*   **Steps:**
    1. Navigate to `/dashboard/patients/registration`.
    2. Enter details: "John Doe", "1990-05-15", Mobile: "555-0101".
    3. Click "Register Patient".
*   **Expected Output:** Patient created successfully. Redirection to Patient Workspace. A `UHID` (e.g., `UHID-202603-XXXX`) is automatically assigned.

### Test Case 2: OPD Encounter & Triage Flow
*   **Role:** Receptionist / Nurse
*   **Steps:**
    1. In the Patient Workspace, click "New Encounter". Selected Type: `OPD`. Department: `General Medicine`.
    2. Route to `/dashboard/opd-visits`. Start AI Intake or normal Triage.
    3. Enter vitals: BP: 140/90, HR: 88, SpO2: 97.
*   **Expected Output:** Patient appears in the smart queue. Vitals are synced to the `Vitals` tab in the Patient Workspace.

### Test Case 3: Doctor Consultation & Clinical Orders
*   **Role:** Doctor
*   **Steps:**
    1. Open the encounter from `Doctor Desk`. 
    2. Enter Diagnosis: "Hypertension / Viral Fever".
    3. Prescribe Medication: "Paracetamol 500mg, 1x3 days".
    4. Order Lab Test: "Complete Blood Count (CBC)".
    5. Save and Close Encounter details.
*   **Expected Output:** 
    - The prescription displays in `/dashboard/pharmacy`.
    - The lab order appears in `/dashboard/lab` beneath `Samples` > `Pending`.

### Test Case 4: LIS Validation Flow
*   **Role:** Lab Technician Let
*   **Steps:**
    1. Navigate to `Lab Information System` (`/dashboard/lab`).
    2. From `Samples`, locate the CBC order for John Doe.
    3. Click "Receive" then "Process".
    4. Enter mock numeric results (e.g., Hemoglobin 14.2 g/dL).
    5. Go to the "Validation" tab, find the result, and click "Validate".
*   **Expected Output:** Result status changes to `VALIDATED`. Looking back at the Patient Workspace > Labs tab shows the generated CBC result.

### Test Case 5: Pharmacy Dispensing Flow
*   **Role:** Pharmacist
*   **Steps:**
    1. Navigate to `Pharmacy Dashboard` (`/dashboard/pharmacy`).
    2. Locate the pending prescription for Paracetamol inside the Rx Worklist.
    3. Verify available inventory stock.
    4. Click "Dispense & Deduct Inventory".
*   **Expected Output:** The prescription transforms to `DISPENSED`. Inventory ledger for the corresponding Paracetamol batch is reduced by exactly 3 tablets.

### Test Case 6: IPD Admission & Bed Allocation
*   **Role:** Doctor & Bed Manager
*   **Steps:**
    1. Doctor clicks "Admit Patient" from the Encounter Workspace. Wait for prompt, fill Priority.
    2. Bed Manager logs in and routes to `/dashboard/ipd/`.
    3. Select "Pending Admissions" tab. Click "Allocate" on John Doe's row.
    4. Select an available bed (e.g., General Ward - GW-01).
*   **Expected Output:** Bed status updates to `Occupied` within `/dashboard/wards`. The Patient Workspace is flagged with an active IPD session.

### Test Case 7: Operating Theatre & Blood Bank Flow (Optional depending on case)
*   **Role:** Surgeon / OT Admin
*   **Steps:**
    1. Navigate to `/ot`. Schedule a new procedure for John Doe.
    2. Go through the Pre-op Checklist and complete all items.
    3. Submit a Blood Request for B+ via Blood Bank module. 
    4. Conclude Surgery, change status to `Completed`.
*   **Expected Output:** The OT dashboard clears the schedule box. Post-op tasks are attached to the IPD Nursing board. Blood bank inventory deducts the respective blood bag unit.

### Test Case 8: Final Billing & Discharge
*   **Role:** Billing Officer
*   **Steps:**
    1. Wait for Doctor to trigger "Discharge Recommendation".
    2. Navigate to `/dashboard/rcm-billing`. Create a new invoice for John Doe's completed IPD encounter.
    3. Ensure charges are dynamically pulled: Consultation fee, CBC Lab Cost, Paracetamol cost, and Bed charges (calculated by hours occupied).
    4. Generate Final Invoice PDF.
*   **Expected Output:** Total aggregate cost matches constituent services. The PDF downloads properly formatted to local system. Encounter marks itself as `Closed`.
