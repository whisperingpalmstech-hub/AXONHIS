#!/usr/bin/env python3
"""
UI Feature Validation Script — v2 (Fixed routes)
Tests every API endpoint that the frontend calls, using the SAME payloads
the React components send. Any failure here = a broken feature in the UI.
"""
import requests, json, uuid, sys
from datetime import datetime, timezone, timedelta

BASE = "http://localhost:9500/api/v1"
PASS = 0
FAIL = 0
ERRORS = []

def log_result(feature, endpoint, method, ok, detail=""):
    global PASS, FAIL
    status = "✅ PASS" if ok else "❌ FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
        ERRORS.append(f"[{feature}] {method} {endpoint}: {detail}")
    print(f"  {status}  {feature:<45} {method} {endpoint}")
    if detail and not ok:
        print(f"         └── {detail[:200]}")

# ─── AUTH ───
print("\n" + "="*80)
print("  UI FEATURE VALIDATION v2 — Testing all frontend-facing API endpoints")
print("="*80 + "\n")

print("[AUTH] Logging in...")
r = requests.post(f"{BASE}/auth/login", json={"email": "admin@riv-hlt1.com", "password": "Admin@1234"})
if not r.ok:
    print(f"❌ FATAL: Login failed: {r.text}")
    sys.exit(1)
TOKEN = r.json()["access_token"]
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
print(f"  ✅ Authenticated.\n")

# ═══════════════════════════════════════════════════════════════════
# 1. PATIENT REGISTRATION (registration/page.tsx)
# ═══════════════════════════════════════════════════════════════════
print("─" * 60)
print("[MODULE 1] Patient Registration")
print("─" * 60)

uid = str(uuid.uuid4())[:6]
patient_payload = {
    "first_name": f"UITest{uid}",
    "last_name": "Patient",
    "date_of_birth": "1990-05-15",
    "gender": "Male",
    "primary_phone": f"98765{uid[:5].replace('-','')}",
    "email": f"uitest{uid}@test.com"
}
r = requests.post(f"{BASE}/patients/", json=patient_payload, headers=H)
log_result("Patient Registration", "/patients/", "POST", r.ok, r.text if not r.ok else "")
patient_id = r.json().get("id") if r.ok else None

if patient_id:
    r2 = requests.post(f"{BASE}/patients/{patient_id}/identifiers/", json={
        "identifier_type": "national_id", "identifier_value": f"AADH-{uid}"
    }, headers=H)
    log_result("Add Identifier (Aadhaar)", f"/patients/.../identifiers/", "POST", r2.ok, r2.text if not r2.ok else "")

    r3 = requests.post(f"{BASE}/patients/{patient_id}/insurance/", json={
        "insurance_provider": "Star Health", "policy_number": f"POL-{uid}"
    }, headers=H)
    log_result("Add Patient Insurance", f"/patients/.../insurance/", "POST", r3.ok, r3.text if not r3.ok else "")

    r4 = requests.get(f"{BASE}/patients/{patient_id}", headers=H)
    log_result("Get Patient Profile", f"/patients/{{id}}", "GET", r4.ok, r4.text if not r4.ok else "")

    r5 = requests.get(f"{BASE}/patients/search?query=UITest&limit=5", headers=H)
    log_result("Patient Search", "/patients/search?query=UITest", "GET", r5.ok, r5.text if not r5.ok else "")

# ═══════════════════════════════════════════════════════════════════
# 2. DOCTOR DESK (doctor-desk/page.tsx) — FIXED routes
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("[MODULE 2] Doctor Desk")
print("─" * 60)

DOCTOR_ID = "00000000-0000-0000-0000-000000000009"

r = requests.get(f"{BASE}/doctor-desk/worklist/{DOCTOR_ID}", headers=H)
log_result("Doctor Worklist", f"/doctor-desk/worklist/{{doc_id}}", "GET", r.ok, r.text if not r.ok else "")

if patient_id:
    r = requests.post(f"{BASE}/doctor-desk/worklist", json={
        "doctor_id": DOCTOR_ID,
        "visit_id": "00000000-0000-0000-0000-000000000000",
        "patient_id": patient_id,
        "priority_indicator": "normal"
    }, headers=H)
    log_result("Seed Patient to Doctor Queue", "/doctor-desk/worklist", "POST", r.ok, r.text if not r.ok else "")
    wl_id = r.json().get("id") if r.ok else None

    # FIX: status is a QUERY PARAM, not JSON body (frontend: ?status=in_consultation)
    if wl_id:
        r = requests.put(f"{BASE}/doctor-desk/worklist/{wl_id}/status?status=in_consultation", headers=H)
        log_result("Update Worklist Status", f"/doctor-desk/worklist/.../status?status=...", "PUT", r.ok, r.text if not r.ok else "")

    # FIX: Save note route is /scribe, not /notes (frontend: doctorDeskApi.saveNote -> /doctor-desk/scribe)
    r = requests.post(f"{BASE}/doctor-desk/scribe", json={
        "chief_complaint": "Fever and body ache for 3 days",
        "history_present_illness": "Patient reports high-grade intermittent fever",
        "plan": "Order CBC, start paracetamol",
        "doctor_id": DOCTOR_ID,
        "visit_id": "00000000-0000-0000-0000-000000000000"
    }, headers=H)
    log_result("Save Doctor Note (Scribe)", "/doctor-desk/scribe", "POST", r.ok, r.text if not r.ok else "")

    # FIX: AI suggestions route is /ai/suggestions, not /ai-suggestions
    r = requests.post(f"{BASE}/doctor-desk/ai/suggestions", json={
        "visit_id": "00000000-0000-0000-0000-000000000000",
        "symptoms": "Fever and body ache for 3 days"
    }, headers=H)
    log_result("AI Diagnostic Suggestions", "/doctor-desk/ai/suggestions", "POST", r.ok, r.text if not r.ok else "")

    r = requests.post(f"{BASE}/doctor-desk/orders", json={
        "visit_id": "00000000-0000-0000-0000-000000000000",
        "doctor_id": DOCTOR_ID,
        "order_type": "Laboratory",
        "test_name": "Complete Blood Count"
    }, headers=H)
    log_result("Place Diagnostic Order", "/doctor-desk/orders", "POST", r.ok, r.text if not r.ok else "")

    r = requests.get(f"{BASE}/doctor-desk/timeline/{patient_id}", headers=H)
    log_result("Get Clinical Timeline", f"/doctor-desk/timeline/{{patient_id}}", "GET", r.ok, r.text if not r.ok else "")

# ═══════════════════════════════════════════════════════════════════
# 3. IPD WORKFLOW — FIXED routes
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("[MODULE 3] IPD Admission & Bed Management")
print("─" * 60)

adm_no = None
if patient_id:
    ipd_req = {
        "patient_name": f"UITest{uid} Patient",
        "patient_uhid": patient_id,
        "gender": "Male",
        "date_of_birth": "1990-05-15",
        "mobile_number": "9876543210",
        "admitting_doctor": "Dr. UI Test",
        "treating_doctor": "Dr. UI Test",
        "specialty": "General Medicine",
        "reason_for_admission": "Acute renal colic",
        "admission_category": "Emergency",
        "admission_source": "OPD",
        "preferred_bed_category": "General Ward",
        "expected_admission_date": datetime.now(timezone.utc).isoformat(),
        "clinical_notes": "Pain in left flank radiating to groin"
    }
    r = requests.post(f"{BASE}/ipd/requests", json=ipd_req, headers=H)
    log_result("IPD Admission Request", "/ipd/requests", "POST", r.ok, r.text if not r.ok else "")
    req_id = r.json().get("id") if r.ok else None

    # FIX: Approval uses PUT /requests/{req_id}/status?new_status=Approved (query param)
    if req_id:
        r = requests.put(f"{BASE}/ipd/requests/{req_id}/status?new_status=Approved", headers=H)
        log_result("IPD Request Approval", f"/ipd/requests/.../status?new_status=Approved", "PUT", r.ok, r.text if not r.ok else "")

    # Always create a fresh bed to guarantee availability
    bed_code = None
    wuid = str(uuid.uuid4())[:4]
    # Ward: requires ward_code, ward_name, department, capacity
    rw = requests.post(f"{BASE}/wards/", json={
        "ward_code": f"WD-{wuid}", "ward_name": f"UI Ward {wuid}",
        "department": "General Medicine", "capacity": 10
    }, headers=H)
    if rw.ok:
        ward_id = rw.json().get("id")
        # Room: requires ward_id, room_number, room_type, capacity
        rr = requests.post(f"{BASE}/wards/rooms", json={
            "ward_id": str(ward_id), "room_number": f"R-{wuid}",
            "room_type": "general", "capacity": 2
        }, headers=H)
        if rr.ok:
            room_id = rr.json().get("id")
            # Bed: requires room_id, bed_code, bed_number, bed_type, status
            rb = requests.post(f"{BASE}/wards/beds", json={
                "room_id": str(room_id), "bed_code": f"BED-{wuid}",
                "bed_number": f"B1-{wuid}", "bed_type": "standard", "status": "available"
            }, headers=H)
            if rb.ok:
                bed_code = rb.json().get("bed_code")
            else:
                log_result("Create Bed (step 3/3)", "/wards/beds", "POST", False, rb.text)
        else:
            log_result("Create Room (step 2/3)", "/wards/rooms", "POST", False, rr.text)
    else:
        log_result("Create Ward (step 1/3)", "/wards/", "POST", False, rw.text)
    log_result("Create Fresh Bed", "/wards/beds", "POST", bed_code is not None, "Bed creation failed" if not bed_code else f"BED-{wuid}")

    # FIX: Allocation is POST /requests/{req_id}/allocate/{bed_code} (frontend pattern)
    if bed_code and req_id:
        r = requests.post(f"{BASE}/ipd/requests/{req_id}/allocate/{bed_code}", headers=H)
        log_result("IPD Bed Allocation", f"/ipd/requests/.../allocate/{bed_code}", "POST", r.ok, r.text if not r.ok else "")
        if r.ok:
            adm_no = r.json().get("admission_number")
            print(f"         └── Admission #: {adm_no}")

# ═══════════════════════════════════════════════════════════════════
# 4. IPD BILLING (ipd-billing/page.tsx)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("[MODULE 4] IPD Billing & Insurance")
print("─" * 60)

if adm_no:
    r = requests.get(f"{BASE}/ipd/billing/dashboard", headers=H)
    log_result("Billing Dashboard", "/ipd/billing/dashboard", "GET", r.ok, r.text if not r.ok else "")

    r = requests.get(f"{BASE}/ipd/billing/{adm_no}", headers=H)
    log_result("Billing Master Record", f"/ipd/billing/{{adm_no}}", "GET", r.ok, r.text if not r.ok else "")

    r = requests.post(f"{BASE}/ipd/billing/{adm_no}/services", json={
        "service_category": "Room & Nursing",
        "service_name": "General Ward - Per Day",
        "quantity": 2,
        "unit_price": 1500.00
    }, headers=H)
    log_result("Add Service Charge", f"/ipd/billing/.../services", "POST", r.ok, r.text if not r.ok else "")

    r = requests.post(f"{BASE}/ipd/billing/{adm_no}/deposits", json={
        "amount": 3000.00,
        "payment_mode": "Cash",
        "reference_number": ""
    }, headers=H)
    log_result("Collect Advance Deposit", f"/ipd/billing/.../deposits", "POST", r.ok, r.text if not r.ok else "")

    r = requests.post(f"{BASE}/ipd/billing/{adm_no}/insurance", json={
        "insurance_provider": "Star Health Insurance",
        "policy_number": f"POL-UI-{uid}",
        "pre_auth_number": f"PA-UI-{uid}",
        "coverage_limit": 50000.00,
        "claimed_amount": 3000.00
    }, headers=H)
    log_result("File Insurance Claim", f"/ipd/billing/.../insurance", "POST", r.ok, r.text if not r.ok else "")
    claim_id = r.json().get("id") if r.ok else None

    if claim_id:
        r = requests.post(f"{BASE}/ipd/billing/insurance/{claim_id}/approve", json={
            "approved_amount": 3000.00,
            "status": "Approved"
        }, headers=H)
        log_result("Approve Insurance Claim (TPA)", f"/ipd/billing/insurance/.../approve", "POST", r.ok, r.text if not r.ok else "")

    r = requests.get(f"{BASE}/ipd/billing/{adm_no}/available-insurance", headers=H)
    log_result("Available Insurance Lookup", f"/ipd/billing/.../available-insurance", "GET", r.ok, r.text if not r.ok else "")

    r = requests.post(f"{BASE}/ipd/billing/{adm_no}/recalculate", json={}, headers=H)
    log_result("Recalculate Bill", f"/ipd/billing/.../recalculate", "POST", r.ok, r.text if not r.ok else "")
    if r.ok:
        b = r.json()
        print(f"         └── Charges: ₹{b.get('total_charges',0):.2f} | Insurance: ₹{b.get('insurance_payable',0):.2f} | Patient: ₹{b.get('patient_payable',0):.2f} | Outstanding: ₹{b.get('outstanding_balance',0):.2f}")

    r = requests.post(f"{BASE}/ipd/billing/{adm_no}/payments", json={
        "amount": 500.00,
        "payment_mode": "Card",
        "reference_number": "TXN-UI-TEST"
    }, headers=H)
    log_result("Process Payment", f"/ipd/billing/.../payments", "POST", r.ok, r.text if not r.ok else "")
else:
    print("  ⚠ Skipped (no admission number available)")

# ═══════════════════════════════════════════════════════════════════
# 5. IPD NURSING & DOCTOR DESK
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("[MODULE 5] IPD Nursing & Clinical Documentation")
print("─" * 60)

if adm_no:
    # Vitals route is /ipd/vitals/{adm_no}, not /ipd/nursing/vitals/
    r = requests.post(f"{BASE}/ipd/vitals/{adm_no}", json={
        "temperature": 98.6, "pulse_rate": 78, "bp_systolic": 120, "bp_diastolic": 80,
        "respiratory_rate": 18, "spo2": 98, "weight_kg": 70, "height_cm": 170,
        "pain_score": 3, "recorded_by": "Nurse UI Test"
    }, headers=H)
    log_result("Record Nursing Vitals", f"/ipd/vitals/{{adm_no}}", "POST", r.ok, r.text if not r.ok else "")

    # Diagnosis: icd10_code (not icd_code), description (not diagnosis_description)
    r = requests.post(f"{BASE}/ipd/doctor/diagnoses/{adm_no}", json={
        "icd10_code": "J06.9",
        "description": "Acute upper respiratory infection",
        "diagnosis_type": "Confirmed"
    }, headers=H)
    log_result("Add IPD Diagnosis", f"/ipd/doctor/diagnoses/{{adm_no}}", "POST", r.ok, r.text if not r.ok else "")

    # Treatment: therapy_type (not treatment_type), instructions (not description)
    r = requests.post(f"{BASE}/ipd/doctor/treatment-plans/{adm_no}", json={
        "therapy_type": "Medication",
        "instructions": "IV antibiotics and hydration for 3 days"
    }, headers=H)
    log_result("Add Treatment Plan", f"/ipd/doctor/treatment-plans/{{adm_no}}", "POST", r.ok, r.text if not r.ok else "")
else:
    print("  ⚠ Skipped (no admission number available)")

# ═══════════════════════════════════════════════════════════════════
# 6. BLOOD BANK (blood-bank/page.tsx)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("[MODULE 6] Blood Bank")
print("─" * 60)

bb_uid = str(uuid.uuid4())[:6]

r = requests.post(f"{BASE}/blood-bank/donors", json={
    "donor_id": f"DNR-UI-{bb_uid}",
    "first_name": "UIBlood", "last_name": "Donor",
    "date_of_birth": "1988-03-20",
    "blood_group": "B", "rh_factor": "+",
    "contact_number": "5551234567",
    "screening_status": "eligible"
}, headers=H)
log_result("Register Blood Donor", "/blood-bank/donors", "POST", r.ok, r.text if not r.ok else "")
bb_donor_id = r.json().get("id") if r.ok else None

if bb_donor_id:
    r = requests.post(f"{BASE}/blood-bank/donors/{bb_donor_id}/collections", json={
        "donor_id": str(bb_donor_id),
        "collection_date": datetime.now(timezone.utc).isoformat(),
        "collection_location": "Main Center",
        "collected_by": "Phlebotomist",
        "collection_volume": 450,
        "screening_results": {"hiv": "negative", "hbsag": "negative", "hcv": "negative"}
    }, headers=H)
    log_result("Log Blood Collection", f"/blood-bank/donors/.../collections", "POST", r.ok, r.text if not r.ok else "")
    collection_id = r.json().get("id") if r.ok else None

    if collection_id:
        r = requests.post(f"{BASE}/blood-bank/inventory", json={
            "unit_id": f"BAG-UI-{bb_uid}",
            "blood_group": "B", "rh_factor": "+",
            "collection_id": str(collection_id),
            "collection_date": datetime.now(timezone.utc).isoformat(),
            "expiry_date": (datetime.now(timezone.utc) + timedelta(days=35)).isoformat(),
            "status": "available"
        }, headers=H)
        log_result("Add Unit to Inventory", "/blood-bank/inventory", "POST", r.ok, r.text if not r.ok else "")

r = requests.get(f"{BASE}/blood-bank/inventory", headers=H)
log_result("Get Blood Inventory", "/blood-bank/inventory", "GET", r.ok, r.text if not r.ok else "")

r = requests.get(f"{BASE}/blood-bank/donors", headers=H)
log_result("Get Donor Registry", "/blood-bank/donors", "GET", r.ok, r.text if not r.ok else "")

# ═══════════════════════════════════════════════════════════════════
# 7. PHARMACY
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("[MODULE 7] Pharmacy")
print("─" * 60)

r = requests.get(f"{BASE}/pharmacy/prescriptions", headers=H)
log_result("Get Prescriptions", "/pharmacy/prescriptions", "GET", r.ok, r.text if not r.ok else "")

r = requests.get(f"{BASE}/pharmacy/inventory", headers=H)
log_result("Get Pharmacy Inventory", "/pharmacy/inventory", "GET", r.ok, r.text if not r.ok else "")

# ═══════════════════════════════════════════════════════════════════
# 8. ENCOUNTERS — FIXED (added department field)
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("[MODULE 8] Encounters")
print("─" * 60)

if patient_id:
    r = requests.post(f"{BASE}/encounters/", json={
        "patient_id": patient_id,
        "encounter_type": "OPD",
        "department": "General Medicine",
        "visit_reason": "Routine Follow Up"
    }, headers=H)
    log_result("Create Encounter", "/encounters/", "POST", r.ok, r.text if not r.ok else "")

    r = requests.get(f"{BASE}/encounters/", headers=H)
    log_result("List Encounters", "/encounters/", "GET", r.ok, r.text if not r.ok else "")

# ═══════════════════════════════════════════════════════════════════
# 9. RADIOLOGY
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("[MODULE 9] Radiology")
print("─" * 60)

r = requests.get(f"{BASE}/radiology/orders", headers=H)
log_result("Get Radiology Orders", "/radiology/orders", "GET", r.ok, r.text if not r.ok else "")

# ═══════════════════════════════════════════════════════════════════
# 10. WARDS
# ═══════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("[MODULE 10] Wards Management")
print("─" * 60)

r = requests.get(f"{BASE}/wards/", headers=H)
log_result("Get Wards List", "/wards/", "GET", r.ok, r.text if not r.ok else "")

r = requests.get(f"{BASE}/wards/beds", headers=H)
log_result("Get All Beds", "/wards/beds", "GET", r.ok, r.text if not r.ok else "")

# ═══════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print(f"  RESULTS: {PASS} PASSED, {FAIL} FAILED out of {PASS+FAIL} tests")
print("=" * 80)

if ERRORS:
    print(f"\n  ❌ FAILED TESTS ({len(ERRORS)}):")
    for e in ERRORS:
        print(f"    • {e[:150]}")
else:
    print("\n  🎉 ALL FEATURES PASSED! Every UI endpoint is working correctly.")

print()
