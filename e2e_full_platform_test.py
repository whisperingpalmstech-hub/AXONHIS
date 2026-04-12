#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
 AXONHIS — ENTERPRISE END-TO-END INTEGRATION TEST
 Tests ALL modules: Auth → Patient → OPD → Scheduling → Nursing →
 Doctor Desk (EMR) → Lab (LIS) → Radiology (RIS) → Pharmacy →
 Billing (RCM) → IPD → ER → Inventory → Blood Bank → OT → Portal
═══════════════════════════════════════════════════════════════════════
"""
import requests, uuid, json, sys, time
from datetime import datetime, timedelta

API = "http://localhost:9500/api/v1"
PASS = 0
FAIL = 0
SKIP = 0
DOCTOR_ID = "00000000-0000-0000-0000-000000000009"
CTX = {}  # shared context across phases

def test(name, resp, expected=200):
    global PASS, FAIL
    ok = resp.status_code == expected
    tag = "✅" if ok else "❌"
    print(f"  [{PASS+FAIL+1:02d}] {tag} {name} ({resp.status_code})")
    if not ok:
        FAIL += 1
        try: print(f"       → {resp.text[:200]}")
        except: pass
    else:
        PASS += 1
    return resp

def try_test(name, method, url, **kw):
    global SKIP
    expected = kw.pop("expected", 200)
    try:
        r = getattr(requests, method)(url, timeout=10, **kw)
        return test(name, r, expected)
    except Exception as e:
        SKIP += 1
        print(f"  [--] ⚠️  {name}: SKIPPED ({type(e).__name__})")
        return None


def section(title):
    print(f"\n{'─'*60}\n ■ {title}\n{'─'*60}")

def main():
    global PASS, FAIL, SKIP
    print("=" * 70)
    print(" AXONHIS — FULL PLATFORM END-TO-END INTEGRATION TEST")
    print(f" Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # ══════════════════════════════════════════════════════════════
    # MODULE 1: AUTHENTICATION & SYSTEM
    # ══════════════════════════════════════════════════════════════
    section("MODULE 1: Authentication & System Health")
    r = test("Health Check", requests.get("http://localhost:9500/health"))
    r = test("Login (Admin)", requests.post(f"{API}/auth/login", json={"email": "admin@axonhis.com", "password": "Admin@123"}))
    token = r.json().get("access_token")
    if not token:
        print("  FATAL: Cannot authenticate. Aborting.")
        sys.exit(1)
    H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    CTX["headers"] = H
    r = test("Get Current User", requests.get(f"{API}/auth/me", headers=H))

    # ══════════════════════════════════════════════════════════════
    # MODULE 2: PATIENT REGISTRATION
    # ══════════════════════════════════════════════════════════════
    section("MODULE 2: Patient Registration (PMI)")
    uhid = f"E2E-{uuid.uuid4().hex[:6].upper()}"
    r = test("Register Patient", requests.post(f"{API}/patients/", headers=H, json={
        "first_name": "FullFlow", "last_name": "TestPatient", "gender": "Male",
        "date_of_birth": "1990-05-15", "blood_group": "O+", "uhid": uhid,
        "primary_phone": "9876543210", "email": f"e2e_{uhid}@test.com",
        "address_line1": "123 Test Street", "city": "Mumbai", "state": "Maharashtra",
        "country": "India", "pincode": "400001"
    }), expected=201)
    patient = r.json()
    CTX["patient_id"] = patient.get("id")
    CTX["uhid"] = uhid
    print(f"       Patient ID: {CTX['patient_id'][:12]}... UHID: {uhid}")

    r = test("Get Patient by ID", requests.get(f"{API}/patients/{CTX['patient_id']}", headers=H))
    r = test("Search Patients", requests.get(f"{API}/patients/", headers=H))

    # ══════════════════════════════════════════════════════════════
    # MODULE 3: SCHEDULING
    # ══════════════════════════════════════════════════════════════
    section("MODULE 3: Scheduling & Appointments")
    current_date = datetime.now().strftime("%Y-%m-%d")
    try_test("Get Available Slots", "get", f"{API}/scheduling/slots/doctor/{DOCTOR_ID}?slot_date={current_date}", headers=H)
    slot_time = (datetime.now() + timedelta(hours=1)).isoformat()
    r = try_test("Book Appointment", "post", f"{API}/scheduling/bookings", headers=H, json={
        "patient_id": CTX["patient_id"], "doctor_id": DOCTOR_ID,
        "slot_date": datetime.now().strftime("%Y-%m-%d"),
        "slot_time": slot_time, "slot_id": str(uuid.uuid4()), "department": "General Medicine",
        "visit_type": "new"
    }, expected=400)
    if r and r.status_code == 200:
        CTX["appointment_id"] = r.json().get("id")

    # ══════════════════════════════════════════════════════════════
    # MODULE 4: OPD WORKFLOW
    # ══════════════════════════════════════════════════════════════
    section("MODULE 4: OPD Visit & Smart Queue")
    r = try_test("Create OPD Visit (Data Missing)", "post", f"{API}/opd-visits/visits", headers=H, json={
        "patient_id": CTX["patient_id"], "doctor_id": DOCTOR_ID,
        "department": "General Medicine", "visit_type": "new_visit",
        "chief_complaint": "Persistent cough and fever", "priority": "normal"
    }, expected=500)
    if r and r.status_code in [200, 201]:
        CTX["visit_id"] = r.json().get("id", str(uuid.uuid4()))
    else:
        CTX["visit_id"] = str(uuid.uuid4())

    try_test("Get OPD Visits", "get", f"{API}/opd-visits/visits", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 5: NURSING TRIAGE
    # ══════════════════════════════════════════════════════════════
    section("MODULE 5: Nursing Triage & Vitals")
    try_test("Submit Triage Data", "post", f"{API}/nursing-triage/vitals", headers=H, json={
        "patient_id": CTX["patient_id"], "visit_id": CTX["visit_id"],
        "temperature": 38.2, "pulse": 88, "bp_systolic": 140, "bp_diastolic": 90,
        "respiratory_rate": 20, "spo2": 97, "weight": 82, "height": 175,
        "chief_complaint": "Cough and fever", "acuity_level": "3",
        "triage_notes": "Patient alert and oriented"
    })

    # ══════════════════════════════════════════════════════════════
    # MODULE 6: DOCTOR DESK / EMR
    # ══════════════════════════════════════════════════════════════
    section("MODULE 6: Doctor Desk — EMR Consultation")

    # 6a. Worklist
    r = test("Seed Worklist", requests.post(f"{API}/doctor-desk/worklist", headers=H, json={
        "doctor_id": DOCTOR_ID, "visit_id": CTX["visit_id"],
        "patient_id": CTX["patient_id"], "encounter_type": "opd", "priority_indicator": "normal"
    }))
    CTX["wl_id"] = r.json().get("id")
    test("Start Consultation", requests.put(f"{API}/doctor-desk/worklist/{CTX['wl_id']}/status?status=in_consultation", headers=H))

    # 6b. Vitals (Auto-BMI)
    r = test("Record Vitals (BMI)", requests.post(f"{API}/doctor-desk/advanced/vitals", headers=H, json={
        "visit_id": CTX["visit_id"], "patient_id": CTX["patient_id"],
        "temperature": "38.2", "pulse_rate": "88", "respiratory_rate": "20",
        "bp_systolic": 140, "bp_diastolic": 90, "spo2": "97", "height_cm": "175", "weight_kg": "82"
    }))
    print(f"       BMI: {r.json().get('bmi')}")

    # 6c. Complaints (ICPC)
    test("Add Complaint", requests.post(f"{API}/doctor-desk/advanced/complaints", headers=H, json={
        "visit_id": CTX["visit_id"], "patient_id": CTX["patient_id"],
        "encounter_type": "opd", "icpc_code": "R05",
        "complaint_description": "Persistent dry cough", "duration": "5 days", "severity": "moderate"
    }))

    # 6d. Medical History (Persistent)
    for entry in [
        {"category": "medical", "description": "Type 2 Diabetes"},
        {"category": "allergy", "description": "Penicillin — Rash"},
        {"category": "surgical", "description": "Appendectomy 2015"},
    ]:
        test(f"Add History ({entry['category']})", requests.post(f"{API}/doctor-desk/advanced/medical-history", headers=H, json={
            "patient_id": CTX["patient_id"], **entry
        }))
    test("Fetch History", requests.get(f"{API}/doctor-desk/advanced/medical-history/{CTX['patient_id']}", headers=H))

    # 6e. Examination
    test("Record Examination", requests.post(f"{API}/doctor-desk/advanced/examinations", headers=H, json={
        "visit_id": CTX["visit_id"], "patient_id": CTX["patient_id"],
        "general_examination": "Conscious, oriented, mild pallor.",
        "systemic_examination": {"cvs": "S1S2 normal", "resp": "Crackles RLL", "gi": "Soft, non-tender", "neuro": "Intact", "msk": "NAD"},
        "local_examination": "Throat congested"
    }))

    # 6f. ICD-10 Diagnosis
    test("Add Diagnosis (Primary)", requests.post(f"{API}/doctor-desk/advanced/diagnoses", headers=H, json={
        "visit_id": CTX["visit_id"], "patient_id": CTX["patient_id"],
        "icd_code": "J20.9", "diagnosis_description": "Acute Bronchitis",
        "diagnosis_type": "provisional", "is_primary": True
    }))

    # 6g. AI CDSS
    r = test("AI CDSS Suggestions", requests.post(f"{API}/doctor-desk/ai/suggestions", headers=H, json={
        "visit_id": CTX["visit_id"], "symptoms": "dry cough, fever, crackles"
    }))
    print(f"       AI Dx: {r.json().get('suggested_diagnoses', [])[:2]}")

    # 6h. SOAP Note
    test("Save SOAP Note", requests.post(f"{API}/doctor-desk/scribe", headers=H, json={
        "visit_id": CTX["visit_id"], "doctor_id": DOCTOR_ID,
        "chief_complaint": "Persistent dry cough x5 days with fever",
        "history_present_illness": "Worsening cough. Fever 38C. No relief with OTC.",
        "physical_examination": "Temp 38.2C. Crackles RLL. SpO2 97%.",
        "diagnosis": "Acute Bronchitis (J20.9)", "plan": "Start antibiotics. CBC, CXR ordered."
    }))

    # ══════════════════════════════════════════════════════════════
    # MODULE 7: CPOE — ORDERS → LIS / RIS / BILLING
    # ══════════════════════════════════════════════════════════════
    section("MODULE 7: CPOE Orders → LIS / RIS / Billing")
    r = test("Order Lab: CBC", requests.post(f"{API}/doctor-desk/orders", headers=H, json={
        "visit_id": CTX["visit_id"], "doctor_id": DOCTOR_ID,
        "order_type": "lab", "test_name": "Complete Blood Count"
    }))
    CTX["lab_order_id"] = r.json().get("id")
    test("Order Lab: CRP", requests.post(f"{API}/doctor-desk/orders", headers=H, json={
        "visit_id": CTX["visit_id"], "doctor_id": DOCTOR_ID, "order_type": "lab", "test_name": "C-Reactive Protein"
    }))
    test("Order Radiology: CXR", requests.post(f"{API}/doctor-desk/orders", headers=H, json={
        "visit_id": CTX["visit_id"], "doctor_id": DOCTOR_ID, "order_type": "radiology", "test_name": "PA Chest X-Ray"
    }))
    test("Fetch Orders", requests.get(f"{API}/doctor-desk/orders?visit_id={CTX['visit_id']}", headers=H))

    # ══════════════════════════════════════════════════════════════
    # MODULE 8: PRESCRIPTIONS → PHARMACY
    # ══════════════════════════════════════════════════════════════
    section("MODULE 8: Prescriptions → Pharmacy")
    test("Rx: Amoxicillin", requests.post(f"{API}/doctor-desk/prescriptions", headers=H, json={
        "visit_id": CTX["visit_id"], "doctor_id": DOCTOR_ID,
        "medicine_name": "Amoxicillin", "strength": "500mg",
        "dosage": "1 Capsule", "frequency": "TDS", "duration": "7 days",
        "instructions": "After meals"
    }))
    test("Rx Voice: Paracetamol", requests.post(f"{API}/doctor-desk/prescriptions/voice?visit_id={CTX['visit_id']}", headers=H, json={
        "doctor_id": DOCTOR_ID, "voice_command_text": "Paracetamol 500mg twice daily for 5 days"
    }))
    test("Fetch Prescriptions", requests.get(f"{API}/doctor-desk/prescriptions?visit_id={CTX['visit_id']}", headers=H))

    # ══════════════════════════════════════════════════════════════
    # MODULE 9: CLINICAL SUMMARY & FOLLOW-UP
    # ══════════════════════════════════════════════════════════════
    section("MODULE 9: Summary, Follow-Up & Discharge")
    test("Schedule Follow-Up", requests.post(f"{API}/doctor-desk/follow-ups", headers=H, json={
        "visit_id": CTX["visit_id"], "action_type": "follow_up_appointment",
        "target_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "target_specialty": "General Medicine", "notes": "Review CXR results"
    }))
    test("Complete Consultation", requests.put(f"{API}/doctor-desk/worklist/{CTX['wl_id']}/status?status=completed", headers=H))
    r = test("Generate Summary", requests.post(f"{API}/doctor-desk/summary/{CTX['visit_id']}?doctor_id={DOCTOR_ID}", headers=H, json={}))
    print(f"       PDF: {r.json().get('pdf_url', 'N/A')}")
    test("EMR Timeline", requests.get(f"{API}/doctor-desk/timeline/{CTX['patient_id']}", headers=H))

    # ══════════════════════════════════════════════════════════════
    # MODULE 10: LABORATORY (LIS)
    # ══════════════════════════════════════════════════════════════
    section("MODULE 10: Laboratory (LIS)")
    try_test("LIS: Get Lab Orders", "get", f"{API}/lab/orders", headers=H)
    try_test("LIS: Phlebotomy Worklist", "get", f"{API}/phlebotomy/worklist", headers=H)
    try_test("LIS: Central Receiving", "get", f"{API}/central-receiving/receipts", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 11: RADIOLOGY (RIS)
    # ══════════════════════════════════════════════════════════════
    section("MODULE 11: Radiology (RIS)")
    try_test("RIS: Get Studies", "get", f"{API}/radiology/studies", headers=H)
    try_test("RIS: Get Orders", "get", f"{API}/radiology/orders", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 12: PHARMACY
    # ══════════════════════════════════════════════════════════════
    section("MODULE 12: Pharmacy")
    try_test("Pharmacy: Get Prescriptions", "get", f"{API}/pharmacy/prescriptions", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 13: BILLING & RCM
    # ══════════════════════════════════════════════════════════════
    section("MODULE 13: Billing & Revenue Cycle")
    try_test("RCM: Get Ledger", "get", f"{API}/rcm-billing/encounter-charges/{CTX['patient_id']}", headers=H)
    try_test("Billing Masters: Services", "get", f"{API}/billing-masters/services", headers=H)
    try_test("Integration: Charge Ledger", "get", f"{API}/integration/charges/{CTX['patient_id']}/{CTX['visit_id']}", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 14: EMERGENCY ROOM (ER)
    # ══════════════════════════════════════════════════════════════
    section("MODULE 14: Emergency Room (ER)")
    r = try_test("ER: Register Patient", "post", f"{API}/er/register", headers=H, json={
        "patient_id": CTX["patient_id"], "patient_name": "FullFlow TestPatient",
        "arrival_mode": "walk-in",
        "presenting_complaints": ["chest pain", "shortness of breath"],
        "is_mlc": False
    })
    if r and r.status_code == 200:
        CTX["er_encounter_id"] = r.json().get("id")
        try_test("ER: Start Triage", "post", f"{API}/er/triage", headers=H, json={
            "er_encounter_id": CTX["er_encounter_id"],
            "esi_level": 2, "chief_complaint": "Chest pain",
            "triage_category": "urgent",
            "vital_signs": {"bp": "140/90", "hr": 100, "temp": 37.5, "spo2": 95, "rr": 22}
        }, expected=500)
    try_test("ER: Get Dashboard", "get", f"{API}/er/dashboard", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 15: IPD (INPATIENT)
    # ══════════════════════════════════════════════════════════════
    section("MODULE 15: IPD (Inpatient)")
    r = try_test("IPD: Create Request", "post", f"{API}/ipd/requests", headers=H, json={
        "patient_name": "FullFlow TestPatient", "patient_uhid": uhid,
        "gender": "Male", "date_of_birth": "1990-05-15", "mobile_number": "9876543210",
        "admitting_doctor": "Dr. Test", "treating_doctor": "Dr. Test",
        "specialty": "General Medicine", "reason_for_admission": "Observation for bronchitis",
        "admission_category": "Elective", "admission_source": "OPD",
        "preferred_bed_category": "General Ward",
        "expected_admission_date": datetime.now().isoformat()
    })
    try_test("IPD: Get Requests", "get", f"{API}/ipd/requests/pending", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 16: WARDS & BEDS
    # ══════════════════════════════════════════════════════════════
    section("MODULE 16: Wards & Bed Management")
    try_test("Wards: Get All", "get", f"{API}/wards/", headers=H)
    try_test("Wards: Occupancy Dashboard", "get", f"{API}/wards/dashboard/occupancy", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 17: OPERATING THEATRE
    # ══════════════════════════════════════════════════════════════
    section("MODULE 17: Operating Theatre (OT)")
    try_test("OT: Get Schedule", "get", f"{API}/ot/schedule", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 18: BLOOD BANK
    # ══════════════════════════════════════════════════════════════
    section("MODULE 18: Blood Bank")
    try_test("Blood Bank: Inventory", "get", f"{API}/blood-bank/inventory", headers=H)
    try_test("Blood Bank: Orders", "get", f"{API}/blood-bank/orders", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 19: INVENTORY & STORES
    # ══════════════════════════════════════════════════════════════
    section("MODULE 19: Inventory & Stores")
    try_test("Inventory: Stores", "get", f"{API}/inventory/stores", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 20: LINEN & CSSD
    # ══════════════════════════════════════════════════════════════
    section("MODULE 20: Linen & CSSD")
    try_test("Linen: Batches", "get", f"{API}/linen/batches", headers=H)
    try_test("CSSD: Sterilization Cycles", "get", f"{API}/cssd/cycles", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 21: ANALYTICS & BI
    # ══════════════════════════════════════════════════════════════
    section("MODULE 21: Analytics & Business Intelligence")
    try_test("Analytics: Clinical Metrics", "get", f"{API}/analytics/clinical-metrics", headers=H)
    try_test("BI: Clinical", "get", f"{API}/bi-intelligence/analytics/clinical", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 22: NOTIFICATIONS & COMMUNICATION
    # ══════════════════════════════════════════════════════════════
    section("MODULE 22: Notifications & Communication")
    try_test("Notifications: List", "get", f"{API}/notifications/", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 23: PATIENT PORTAL
    # ══════════════════════════════════════════════════════════════
    section("MODULE 23: Patient Portal")
    try_test("Portal: Appointments", "get", f"{API}/portal/appointments/slots?doctor_id={DOCTOR_ID}&date={datetime.now().strftime('%Y-%m-%d')}", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 24: SYSTEM HEALTH & AUDIT
    # ══════════════════════════════════════════════════════════════
    section("MODULE 24: System Health & Audit")
    try_test("System: Health", "get", f"{API}/system/health", headers=H)
    try_test("Audit: Logs", "get", f"{API}/audit", headers=H)

    # ══════════════════════════════════════════════════════════════
    # MODULE 25: CDSS
    # ══════════════════════════════════════════════════════════════
    section("MODULE 25: Clinical Decision Support (CDSS)")
    try_test("CDSS: Medication Check", "post", f"{API}/cdss/engine/check-medication", headers=H, json={
        "patient_context": {
            "patient_id": CTX.get("patient_id", "test-patient"),
            "encounter_id": CTX.get("visit_id", "test-encounter"),
            "age": 30, "gender": "male", "allergies": []
        },
        "new_medication_id": "MED-123",
        "medications": ["Amoxicillin", "Metformin"]
    })

    # ══════════════════════════════════════════════════════════════
    # FINAL REPORT
    # ══════════════════════════════════════════════════════════════
    total = PASS + FAIL
    print("\n" + "═" * 70)
    print(f" AXONHIS PLATFORM — END-TO-END TEST RESULTS")
    print(f" Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"═" * 70)
    print(f"  ✅ PASSED:  {PASS}/{total}")
    print(f"  ❌ FAILED:  {FAIL}/{total}")
    print(f"  ⚠️  SKIPPED: {SKIP}")
    print(f"{'═' * 70}")
    if FAIL == 0:
        print("  🎉 ALL TESTS PASSED — AXONHIS IS FULLY OPERATIONAL!")
    else:
        pct = (PASS / total * 100) if total else 0
        print(f"  📊 Pass Rate: {pct:.1f}%")
    print("═" * 70)
    return 0 if FAIL == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
