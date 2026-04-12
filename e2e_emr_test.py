#!/usr/bin/env python3
"""
EMR Doctor Desk — Full End-to-End Integration Test
Tests the complete clinical consultation lifecycle:
  Registration → Vitals → Complaints → History → Examination → Diagnosis → Orders → Prescriptions → Summary
"""
import requests, uuid, json, sys, time

API = "http://localhost:9500/api/v1"
PASS = 0
FAIL = 0

def test(name, resp, expected_status=200):
    global PASS, FAIL
    ok = resp.status_code == expected_status
    status = "✅ PASS" if ok else f"❌ FAIL (got {resp.status_code})"
    print(f"  [{PASS+FAIL+1:02d}] {name}: {status}")
    if not ok:
        FAIL += 1
        try: print(f"       Detail: {resp.text[:200]}")
        except: pass
    else:
        PASS += 1
    return resp

def main():
    global PASS, FAIL
    print("=" * 70)
    print(" EMR DOCTOR DESK — END-TO-END INTEGRATION TEST")
    print("=" * 70)

    # 1. Login
    print("\n── Phase 1: Authentication ─────────────────────")
    r = test("Login", requests.post(f"{API}/auth/login", json={"email": "admin@axonhis.com", "password": "Admin@123"}))
    token = r.json().get("access_token")
    if not token:
        print("  FATAL: Cannot get token. Backend may be down.")
        sys.exit(1)
    H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 2. Get a patient
    print("\n── Phase 2: Patient Lookup ─────────────────────")
    r = test("Get Patients", requests.get(f"{API}/patients/", headers=H))
    pts = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
    if not pts:
        print("  FATAL: No patients found. Seed patients first.")
        sys.exit(1)
    patient = pts[-1]
    patient_id = patient["id"]
    print(f"       Using: {patient.get('first_name','?')} {patient.get('last_name','?')} (ID: {patient_id[:8]}...)")

    visit_id = str(uuid.uuid4())
    DOCTOR_ID = "00000000-0000-0000-0000-000000000009"

    # 3. Seed Worklist
    print("\n── Phase 3: Doctor Worklist ────────────────────")
    r = test("Seed to Worklist", requests.post(f"{API}/doctor-desk/worklist", headers=H, json={
        "doctor_id": DOCTOR_ID, "visit_id": visit_id, "patient_id": patient_id,
        "encounter_type": "opd", "priority_indicator": "normal"
    }))
    wl_id = r.json().get("id")

    r = test("Get Worklist", requests.get(f"{API}/doctor-desk/worklist/{DOCTOR_ID}", headers=H))

    r = test("Start Consultation", requests.put(f"{API}/doctor-desk/worklist/{wl_id}/status?status=in_consultation", headers=H))

    # 4. Record Vitals (with auto-BMI)
    print("\n── Phase 4: Vitals (Auto-BMI) ──────────────────")
    r = test("Record Vitals", requests.post(f"{API}/doctor-desk/advanced/vitals", headers=H, json={
        "visit_id": visit_id, "patient_id": patient_id,
        "temperature": "38.2", "pulse_rate": "88", "respiratory_rate": "20",
        "bp_systolic": 140, "bp_diastolic": 90, "spo2": "97",
        "height_cm": "175", "weight_kg": "82"
    }))
    bmi = r.json().get("bmi")
    print(f"       Auto-Computed BMI: {bmi}")

    r = test("Fetch Vitals History", requests.get(f"{API}/doctor-desk/advanced/vitals/{visit_id}", headers=H))

    # 5. Clinical Complaints (ICPC)
    print("\n── Phase 5: Clinical Complaints (ICPC) ─────────")
    r = test("Add Complaint 1", requests.post(f"{API}/doctor-desk/advanced/complaints", headers=H, json={
        "visit_id": visit_id, "patient_id": patient_id, "encounter_type": "opd",
        "icpc_code": "R05", "complaint_description": "Persistent dry cough for 5 days",
        "duration": "5 days", "severity": "moderate"
    }))
    r = test("Add Complaint 2", requests.post(f"{API}/doctor-desk/advanced/complaints", headers=H, json={
        "visit_id": visit_id, "patient_id": patient_id, "encounter_type": "opd",
        "icpc_code": "A03", "complaint_description": "Low-grade fever, intermittent",
        "duration": "3 days", "severity": "mild"
    }))
    r = test("Fetch Complaints", requests.get(f"{API}/doctor-desk/advanced/complaints/{visit_id}", headers=H))
    print(f"       Complaint Count: {len(r.json())}")

    # 6. Patient Medical History (Persistent)
    print("\n── Phase 6: Medical History (Persistent) ───────")
    for entry in [
        {"category": "medical", "description": "Type 2 Diabetes Mellitus, diagnosed 2018"},
        {"category": "allergy", "description": "Allergy to Penicillin — Rash"},
        {"category": "surgical", "description": "Appendectomy (2015)"},
        {"category": "family", "description": "Father — Coronary Artery Disease"},
        {"category": "lifestyle", "description": "Ex-smoker, quit 2020. Occasional alcohol."},
    ]:
        r = test(f"Add History ({entry['category']})", requests.post(f"{API}/doctor-desk/advanced/medical-history", headers=H, json={
            "patient_id": patient_id, **entry
        }))

    r = test("Fetch Full History", requests.get(f"{API}/doctor-desk/advanced/medical-history/{patient_id}", headers=H))
    print(f"       History Records: {len(r.json())}")

    # 7. Clinical Examination
    print("\n── Phase 7: Clinical Examination ───────────────")
    r = test("Record Examination", requests.post(f"{API}/doctor-desk/advanced/examinations", headers=H, json={
        "visit_id": visit_id, "patient_id": patient_id,
        "general_examination": "Conscious, oriented, afebrile at exam. Mild pallor.",
        "systemic_examination": {
            "cvs": "S1S2 normal, no murmurs",
            "resp": "Bilateral air entry present. Mild crackles right lower lobe.",
            "gi": "Soft abdomen, non-tender, no organomegaly",
            "neuro": "Higher functions intact. No focal deficit.",
            "msk": "No joint swelling or deformity"
        },
        "local_examination": "Throat mildly congested. No lymphadenopathy."
    }))
    r = test("Fetch Examinations", requests.get(f"{API}/doctor-desk/advanced/examinations/{visit_id}", headers=H))

    # 8. ICD-10 Diagnoses
    print("\n── Phase 8: ICD-10 Diagnoses ───────────────────")
    r = test("Add Primary Diagnosis", requests.post(f"{API}/doctor-desk/advanced/diagnoses", headers=H, json={
        "visit_id": visit_id, "patient_id": patient_id,
        "icd_code": "J20.9", "diagnosis_description": "Acute Bronchitis, unspecified",
        "diagnosis_type": "provisional", "is_primary": True
    }))
    r = test("Add Secondary Diagnosis", requests.post(f"{API}/doctor-desk/advanced/diagnoses", headers=H, json={
        "visit_id": visit_id, "patient_id": patient_id,
        "icd_code": "R50.9", "diagnosis_description": "Fever, unspecified",
        "diagnosis_type": "final", "is_primary": False
    }))
    r = test("Fetch Diagnoses", requests.get(f"{API}/doctor-desk/advanced/diagnoses/{visit_id}", headers=H))
    print(f"       Diagnosis Count: {len(r.json())}")

    # 9. AI Diagnosis Suggestions
    print("\n── Phase 9: AI CDSS Engine ─────────────────────")
    r = test("AI Suggestions (cough+fever)", requests.post(f"{API}/doctor-desk/ai/suggestions", headers=H, json={
        "visit_id": visit_id, "symptoms": "persistent dry cough, low grade fever, mild crackles"
    }))
    ai = r.json()
    print(f"       Suggested Dx: {ai.get('suggested_diagnoses', [])[:2]}")
    print(f"       Suggested Labs: {ai.get('recommended_lab_tests', [])[:2]}")

    # 10. CPOE Orders (→ LIS/RIS + Billing)
    print("\n── Phase 10: CPOE Orders → LIS/RIS/Billing ────")
    r = test("Order Lab: CBC", requests.post(f"{API}/doctor-desk/orders", headers=H, json={
        "visit_id": visit_id, "doctor_id": DOCTOR_ID,
        "order_type": "lab", "test_name": "Complete Blood Count (CBC)"
    }))
    r = test("Order Lab: CRP", requests.post(f"{API}/doctor-desk/orders", headers=H, json={
        "visit_id": visit_id, "doctor_id": DOCTOR_ID,
        "order_type": "lab", "test_name": "C-Reactive Protein (CRP)"
    }))
    r = test("Order Radiology: Chest X-Ray", requests.post(f"{API}/doctor-desk/orders", headers=H, json={
        "visit_id": visit_id, "doctor_id": DOCTOR_ID,
        "order_type": "radiology", "test_name": "PA Chest X-Ray"
    }))
    r = test("Fetch All Orders", requests.get(f"{API}/doctor-desk/orders?visit_id={visit_id}", headers=H))
    print(f"       Total Orders: {len(r.json())}")

    # 11. Prescriptions (→ Pharmacy)
    print("\n── Phase 11: Prescriptions → Pharmacy ─────────")
    r = test("Rx: Amoxicillin", requests.post(f"{API}/doctor-desk/prescriptions", headers=H, json={
        "visit_id": visit_id, "doctor_id": DOCTOR_ID,
        "medicine_name": "Amoxicillin", "strength": "500mg",
        "dosage": "1 Capsule", "frequency": "TDS (Three times daily)", "duration": "7 days",
        "instructions": "After meals"
    }))
    r = test("Rx: Paracetamol (Voice)", requests.post(f"{API}/doctor-desk/prescriptions/voice?visit_id={visit_id}", headers=H, json={
        "doctor_id": DOCTOR_ID, "voice_command_text": "Paracetamol 500mg twice daily for 5 days as needed for fever"
    }))
    r = test("Fetch All Prescriptions", requests.get(f"{API}/doctor-desk/prescriptions?visit_id={visit_id}", headers=H))
    print(f"       Total Rx: {len(r.json())}")

    # 12. SOAP Notes
    print("\n── Phase 12: SOAP Clinical Notes ───────────────")
    r = test("Save SOAP Note", requests.post(f"{API}/doctor-desk/scribe", headers=H, json={
        "visit_id": visit_id, "doctor_id": DOCTOR_ID,
        "chief_complaint": "Persistent dry cough x5 days with mild fever",
        "history_present_illness": "Patient reports worsening cough, productive at times. Low-grade fever 38C. No relief with OTC meds.",
        "physical_examination": "Temp 38.2C. Mild crackles RLL. SpO2 97%.",
        "diagnosis": "Acute Bronchitis (J20.9). R/O Pneumonia.",
        "plan": "Start Amoxicillin 500mg TDS x7d. Paracetamol PRN. CBC, CRP, CXR ordered. Review in 3 days."
    }))

    # 13. Follow-Up Scheduling
    print("\n── Phase 13: Follow-Up Scheduling ──────────────")
    r = test("Schedule Follow-Up", requests.post(f"{API}/doctor-desk/follow-ups", headers=H, json={
        "visit_id": visit_id, "action_type": "follow_up_appointment",
        "target_date": "2026-04-10T10:00:00Z", "target_specialty": "General Medicine",
        "notes": "Review CXR results. Reassess cough. If no improvement, consider CT Thorax."
    }))

    # 14. Complete Consultation & Generate Summary
    print("\n── Phase 14: Complete & Generate Summary ───────")
    r = test("Mark Completed", requests.put(f"{API}/doctor-desk/worklist/{wl_id}/status?status=completed", headers=H))
    r = test("Generate Clinical Summary", requests.post(f"{API}/doctor-desk/summary/{visit_id}?doctor_id={DOCTOR_ID}", headers=H, json={}))
    summary = r.json()
    print(f"       Summary PDF: {summary.get('pdf_url', 'N/A')}")
    content = summary.get("summary_content", {})
    print(f"       Chief Complaint: {content.get('chief_complaint', 'N/A')[:60]}...")
    print(f"       Prescriptions: {len(content.get('prescriptions', []))} items")
    print(f"       Orders: {len(content.get('orders', []))} items")

    # 15. Patient Timeline
    print("\n── Phase 15: EMR Timeline ──────────────────────")
    r = test("Fetch Patient Timeline", requests.get(f"{API}/doctor-desk/timeline/{patient_id}", headers=H))

    # Final Report
    print("\n" + "=" * 70)
    total = PASS + FAIL
    print(f" RESULTS: {PASS}/{total} PASSED | {FAIL} FAILED")
    if FAIL == 0:
        print(" 🎉 ALL TESTS PASSED — EMR Module is FULLY OPERATIONAL!")
    else:
        print(f" ⚠️  {FAIL} test(s) need attention.")
    print("=" * 70)
    return 0 if FAIL == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
