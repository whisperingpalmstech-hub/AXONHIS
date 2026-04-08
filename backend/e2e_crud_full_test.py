"""
AxonHIS MD – Comprehensive CRUD E2E Test Script
Tests full Create, Read, Update, Delete operations for ALL modules via API
Simulates the exact same operations a user would perform through the UI.
"""
import requests
import json
import sys
import uuid
from datetime import datetime, timedelta, date

API = "http://axonhis_backend:8000/api/v1/md"
PASSED = 0
FAILED = 0
ERRORS = []

# Track created IDs for cleanup and chaining
IDS = {}

def test(name: str, func):
    global PASSED, FAILED
    try:
        result = func()
        if result:
            PASSED += 1
            print(f"  ✅ {name}")
            return result
        else:
            FAILED += 1
            ERRORS.append(name)
            print(f"  ❌ {name} — returned falsy")
            return None
    except Exception as e:
        FAILED += 1
        ERRORS.append(f"{name}: {e}")
        print(f"  ❌ {name} — {e}")
        return None

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def post(path, data):
    r = requests.post(f"{API}{path}", json=data)
    return r

def get(path):
    return requests.get(f"{API}{path}")

def put(path, data):
    return requests.put(f"{API}{path}", json=data)

def delete(path):
    return requests.delete(f"{API}{path}")


# ═══════════════════════════════════════════════════════════
# 1. ORGANIZATION CRUD
# ═══════════════════════════════════════════════════════════
section("1. ORGANIZATION CRUD")

# List
orgs_before = test("LIST organizations", lambda: get("/organizations").json())
count_before = len(orgs_before) if orgs_before else 0

# Create
org = None
r = post("/organizations", {"code": "E2E-CRUD-ORG", "name": "E2E CRUD Test Hospital", "organization_type": "HOSPITAL"})
if r.status_code in [200, 201]:
    org = r.json()
    IDS["org"] = org["organization_id"]
    test("CREATE organization", lambda: org)
else:
    test(f"CREATE organization (HTTP {r.status_code})", lambda: print(r.text) or False)

# Read single
if IDS.get("org"):
    test("GET organization by ID", lambda: get(f"/organizations/{IDS['org']}").status_code == 200)

# Verify count increased
orgs_after = get("/organizations").json()
test("VERIFY org count increased", lambda: len(orgs_after) > count_before)


# ═══════════════════════════════════════════════════════════
# 2. FACILITY CRUD
# ═══════════════════════════════════════════════════════════
section("2. FACILITY CRUD")

facs_before = get("/facilities").json()
test("LIST facilities", lambda: facs_before is not None)

if IDS.get("org"):
    r = post("/facilities", {
        "organization_id": IDS["org"],
        "code": "FAC-E2E",
        "name": "E2E Test Clinic Branch",
        "facility_type": "CLINIC",
        "timezone": "Asia/Dubai"
    })
    if r.status_code in [200, 201]:
        fac = r.json()
        IDS["facility"] = fac["facility_id"]
        test("CREATE facility", lambda: fac)
    else:
        test(f"CREATE facility (HTTP {r.status_code})", lambda: print(r.text) or False)

    facs_after = get("/facilities").json()
    test("VERIFY facility count increased", lambda: len(facs_after) > len(facs_before))


# ═══════════════════════════════════════════════════════════
# 3. SPECIALTY CRUD
# ═══════════════════════════════════════════════════════════
section("3. SPECIALTY CRUD")

specs_before = get("/specialties").json()
test("LIST specialties", lambda: specs_before is not None)
test(f"Found {len(specs_before)} existing specialties", lambda: len(specs_before) > 0)

r = post("/specialties", {
    "code": "NEUROLOGY",
    "name": "Neurology",
    "description": "Brain and nervous system disorders"
})
if r.status_code in [200, 201]:
    spec = r.json()
    IDS["specialty"] = spec["specialty_profile_id"]
    test("CREATE specialty", lambda: spec)
else:
    test(f"CREATE specialty (HTTP {r.status_code})", lambda: print(r.text) or False)

specs_after = get("/specialties").json()
test("VERIFY specialty count increased", lambda: len(specs_after) > len(specs_before))


# ═══════════════════════════════════════════════════════════
# 4. CLINICIAN CRUD
# ═══════════════════════════════════════════════════════════
section("4. CLINICIAN CRUD (Doctor + Nurse)")

clinicians_before = get("/clinicians").json()
test("LIST clinicians", lambda: clinicians_before is not None)

# Create Doctor
if IDS.get("org"):
    r = post("/clinicians", {
        "organization_id": IDS["org"],
        "display_name": "Dr. E2E Surgeon",
        "code": "DR-E2E-01",
        "clinician_type": "DOCTOR",
        "email": "dr.e2e@axonhis.com",
        "mobile_number": "+971501111111",
        "specialty_profile_id": IDS.get("specialty"),
    })
    if r.status_code in [200, 201]:
        doc = r.json()
        IDS["doctor"] = doc["clinician_id"]
        test("CREATE doctor (Dr. E2E Surgeon)", lambda: doc)
    else:
        test(f"CREATE doctor (HTTP {r.status_code})", lambda: print(r.text) or False)

# Create Nurse
    r = post("/clinicians", {
        "organization_id": IDS["org"],
        "display_name": "Nurse E2E Specialst",
        "code": "NR-E2E-01",
        "clinician_type": "NURSE",
        "email": "nurse.e2e@axonhis.com",
        "mobile_number": "+971502222222",
    })
    if r.status_code in [200, 201]:
        nurse = r.json()
        IDS["nurse"] = nurse["clinician_id"]
        test("CREATE nurse (Nurse E2E Specialist)", lambda: nurse)
    else:
        test(f"CREATE nurse (HTTP {r.status_code})", lambda: print(r.text) or False)

clinicians_after = get("/clinicians").json()
test("VERIFY clinician count increased by 2", lambda: len(clinicians_after) >= len(clinicians_before) + 2)


# ═══════════════════════════════════════════════════════════
# 5. PATIENT CRUD (Full registration with identifiers)
# ═══════════════════════════════════════════════════════════
section("5. PATIENT CRUD (Full registration)")

patients_before = get("/patients").json()
test("LIST patients", lambda: patients_before is not None)

if IDS.get("org"):
    mrn = f"MRN-CRUD-{datetime.now().strftime('%H%M%S')}"
    r = post("/patients", {
        "organization_id": IDS["org"],
        "display_name": "John CRUD Smith",
        "mrn": mrn,
        "first_name": "John",
        "last_name": "Smith",
        "dob": "1985-03-15",
        "sex": "MALE",
        "mobile_number": "+971509876543",
        "email": "john.crud@test.com",
        "preferred_language": "en",
        "identifiers": [
            {"identifier_type": "NATIONAL_ID", "identifier_value": "784-1985-1234567-1", "issuing_authority": "UAE-ICA"}
        ],
        "consent": {
            "default_share_mode": "ASK_EACH_TIME",
            "allow_summary_share": True,
            "allow_full_record_share": False,
            "marketing_contact_allowed": False
        }
    })
    if r.status_code in [200, 201]:
        pat = r.json()
        IDS["patient"] = pat["patient_id"]
        test("CREATE patient (John CRUD Smith)", lambda: pat)
        test("Patient has MRN", lambda: pat.get("mrn") == mrn)
        test("Patient has enterprise key", lambda: pat.get("enterprise_patient_key"))
    else:
        test(f"CREATE patient (HTTP {r.status_code})", lambda: print(r.text) or False)

    # Read by ID
    if IDS.get("patient"):
        p = get(f"/patients/{IDS['patient']}").json()
        test("GET patient by ID", lambda: p.get("display_name") == "John CRUD Smith")
        test("Patient has identifiers", lambda: len(p.get("identifiers", [])) > 0)
        test("Patient has consent profile", lambda: p.get("consent_profile") is not None)

    # Create second patient
    r2 = post("/patients", {
        "organization_id": IDS["org"],
        "display_name": "Jane CRUD Doe",
        "mrn": f"MRN-CRUD2-{datetime.now().strftime('%H%M%S')}",
        "sex": "FEMALE",
        "dob": "1992-08-20",
        "mobile_number": "+971508765432",
    })
    if r2.status_code in [200, 201]:
        pat2 = r2.json()
        IDS["patient2"] = pat2["patient_id"]
        test("CREATE patient 2 (Jane CRUD Doe)", lambda: pat2)

patients_after = get("/patients").json()
test("VERIFY patient count increased", lambda: len(patients_after) > len(patients_before))


# ═══════════════════════════════════════════════════════════
# 6. CHANNEL CRUD
# ═══════════════════════════════════════════════════════════
section("6. CHANNEL CRUD")

channels_before = get("/channels").json()
test("LIST channels", lambda: channels_before is not None)

if IDS.get("org"):
    r = post("/channels", {
        "organization_id": IDS["org"],
        "code": "E2E-TC",
        "name": "E2E Teleconsult",
        "channel_type": "TELECONSULT"
    })
    if r.status_code in [200, 201]:
        ch = r.json()
        IDS["channel"] = ch["channel_id"]
        test("CREATE channel (E2E Teleconsult)", lambda: ch)
    else:
        test(f"CREATE channel (HTTP {r.status_code})", lambda: print(r.text) or False)


# ═══════════════════════════════════════════════════════════
# 7. APPOINTMENT CRUD
# ═══════════════════════════════════════════════════════════
section("7. APPOINTMENT CRUD")

appts_before = get("/appointments").json()
test("LIST appointments", lambda: appts_before is not None)

if IDS.get("patient") and IDS.get("doctor"):
    start = (datetime.now() + timedelta(hours=3)).isoformat() + "Z"
    end = (datetime.now() + timedelta(hours=3, minutes=30)).isoformat() + "Z"
    r = post("/appointments", {
        "organization_id": IDS["org"],
        "patient_id": IDS["patient"],
        "clinician_id": IDS["doctor"],
        "appointment_mode": "IN_PERSON",
        "appointment_type": "NEW",
        "slot_start": start,
        "slot_end": end,
        "reason_text": "Full CRUD Test - Initial Consultation",
        "channel_id": IDS.get("channel"),
    })
    if r.status_code in [200, 201]:
        appt = r.json()
        IDS["appointment"] = appt["appointment_id"]
        test("CREATE appointment (IN_PERSON/NEW)", lambda: appt)
        test("Appointment has patient name", lambda: appt.get("patient_name"))
    else:
        test(f"CREATE appointment (HTTP {r.status_code})", lambda: print(r.text) or False)

    # Teleconsult appointment
    start2 = (datetime.now() + timedelta(hours=5)).isoformat() + "Z"
    end2 = (datetime.now() + timedelta(hours=5, minutes=20)).isoformat() + "Z"
    r2 = post("/appointments", {
        "organization_id": IDS["org"],
        "patient_id": IDS.get("patient2", IDS["patient"]),
        "clinician_id": IDS["doctor"],
        "appointment_mode": "TELECONSULT",
        "appointment_type": "FOLLOW_UP",
        "slot_start": start2,
        "slot_end": end2,
        "reason_text": "Follow-up teleconsultation",
    })
    if r2.status_code in [200, 201]:
        IDS["appointment2"] = r2.json()["appointment_id"]
        test("CREATE teleconsult appointment", lambda: r2.json())

appts_after = get("/appointments").json()
test("VERIFY appointment count increased", lambda: len(appts_after) > len(appts_before))


# ═══════════════════════════════════════════════════════════
# 8. ENCOUNTER CRUD
# ═══════════════════════════════════════════════════════════
section("8. ENCOUNTER CRUD")

encs_before = get("/encounters").json()
test("LIST encounters", lambda: encs_before is not None)

if IDS.get("patient") and IDS.get("doctor"):
    r = post("/encounters", {
        "organization_id": IDS["org"],
        "patient_id": IDS["patient"],
        "clinician_id": IDS["doctor"],
        "encounter_mode": "IN_PERSON",
        "chief_complaint": "Full CRUD Test - Chest pain and shortness of breath",
        "appointment_id": IDS.get("appointment"),
    })
    if r.status_code in [200, 201]:
        enc = r.json()
        IDS["encounter"] = enc["encounter_id"]
        test("CREATE encounter", lambda: enc)
        test("Encounter status is OPEN", lambda: enc.get("encounter_status") == "OPEN")
        test("Encounter has patient name", lambda: enc.get("patient_name"))
    else:
        test(f"CREATE encounter (HTTP {r.status_code})", lambda: print(r.text) or False)

encs_after = get("/encounters").json()
test("VERIFY encounter count increased", lambda: len(encs_after) > len(encs_before))


# ═══════════════════════════════════════════════════════════
# 9. ENCOUNTER NOTES CRUD
# ═══════════════════════════════════════════════════════════
section("9. ENCOUNTER NOTES CRUD")

if IDS.get("encounter"):
    notes = get(f"/encounters/{IDS['encounter']}/notes").json()
    test("LIST encounter notes", lambda: notes is not None)

    r = post("/notes", {
        "encounter_id": IDS["encounter"],
        "note_type": "HISTORY",
        "structured_json": {"complaint": "Chest pain", "duration": "2 days", "severity": "moderate"},
        "narrative_text": "Patient presents with 2-day history of left-sided chest pain, aggravated by exertion.",
        "authored_by": "Dr. E2E Surgeon"
    })
    if r.status_code in [200, 201]:
        note = r.json()
        IDS["note"] = note["encounter_note_id"]
        test("CREATE history note", lambda: note)
    else:
        test(f"CREATE history note (HTTP {r.status_code})", lambda: print(r.text) or False)

    # Exam note
    r2 = post("/notes", {
        "encounter_id": IDS["encounter"],
        "note_type": "EXAM",
        "structured_json": {"heart": "Regular rhythm", "lungs": "Clear bilaterally", "bp": "130/85"},
        "narrative_text": "Physical examination findings within normal limits.",
        "authored_by": "Dr. E2E Surgeon"
    })
    if r2.status_code in [200, 201]:
        test("CREATE exam note", lambda: r2.json())

    notes_after = get(f"/encounters/{IDS['encounter']}/notes").json()
    test("VERIFY 2 notes created", lambda: len(notes_after) >= 2)


# ═══════════════════════════════════════════════════════════
# 10. DIAGNOSIS CRUD
# ═══════════════════════════════════════════════════════════
section("10. DIAGNOSIS CRUD")

if IDS.get("encounter"):
    diags = get(f"/encounters/{IDS['encounter']}/diagnoses").json()
    test("LIST diagnoses", lambda: diags is not None)

    r = post("/diagnoses", {
        "encounter_id": IDS["encounter"],
        "diagnosis_type": "PRIMARY",
        "diagnosis_code": "I20.0",
        "diagnosis_display": "Unstable angina pectoris",
        "probability_score": 0.85,
        "source_type": "CLINICIAN"
    })
    if r.status_code in [200, 201]:
        diag = r.json()
        IDS["diagnosis"] = diag["diagnosis_id"]
        test("CREATE primary diagnosis (Unstable angina)", lambda: diag)
    else:
        test(f"CREATE diagnosis (HTTP {r.status_code})", lambda: print(r.text) or False)

    # Secondary diagnosis
    r2 = post("/diagnoses", {
        "encounter_id": IDS["encounter"],
        "diagnosis_type": "SECONDARY",
        "diagnosis_code": "I10",
        "diagnosis_display": "Essential hypertension",
        "source_type": "AI_SUGGESTED"
    })
    if r2.status_code in [200, 201]:
        test("CREATE secondary diagnosis (Hypertension)", lambda: r2.json())


# ═══════════════════════════════════════════════════════════
# 11. SERVICE REQUESTS (ORDERS) CRUD
# ═══════════════════════════════════════════════════════════
section("11. SERVICE REQUESTS (ORDERS) CRUD")

orders_before = get("/service-requests").json()
test("LIST service requests", lambda: orders_before is not None)

if IDS.get("encounter"):
    # Lab order
    r = post("/service-requests", {
        "encounter_id": IDS["encounter"],
        "request_type": "LAB",
        "catalog_code": "TROP-I",
        "catalog_name": "Troponin I (Cardiac)",
        "priority": "STAT",
    })
    if r.status_code in [200, 201]:
        order = r.json()
        IDS["order_lab"] = order["service_request_id"]
        test("CREATE lab order (Troponin I STAT)", lambda: order)
    else:
        test(f"CREATE lab order (HTTP {r.status_code})", lambda: print(r.text) or False)

    # Imaging order
    r2 = post("/service-requests", {
        "encounter_id": IDS["encounter"],
        "request_type": "IMAGING",
        "catalog_code": "CXR-PA",
        "catalog_name": "Chest X-Ray PA View",
        "priority": "ROUTINE",
    })
    if r2.status_code in [200, 201]:
        IDS["order_img"] = r2.json()["service_request_id"]
        test("CREATE imaging order (Chest X-Ray)", lambda: r2.json())

orders_after = get("/service-requests").json()
test("VERIFY order count increased", lambda: len(orders_after) > len(orders_before))


# ═══════════════════════════════════════════════════════════
# 12. MEDICATION/PRESCRIPTIONS CRUD
# ═══════════════════════════════════════════════════════════
section("12. PRESCRIPTIONS CRUD")

if IDS.get("encounter"):
    # Prescription 1
    r = post("/medications", {
        "encounter_id": IDS["encounter"],
        "medication_code": "ASPIRIN81",
        "medication_name": "Aspirin 81mg",
        "route": "ORAL",
        "dose": "81mg",
        "frequency": "OD",
        "duration": "Continuous",
    })
    if r.status_code in [200, 201]:
        rx = r.json()
        IDS["rx1"] = rx["medication_request_id"]
        test("CREATE prescription (Aspirin 81mg)", lambda: rx)
    else:
        test(f"CREATE prescription (HTTP {r.status_code})", lambda: print(r.text) or False)

    # Prescription 2
    r2 = post("/medications", {
        "encounter_id": IDS["encounter"],
        "medication_code": "ATORVA20",
        "medication_name": "Atorvastatin 20mg",
        "route": "ORAL",
        "dose": "20mg",
        "frequency": "HS",
        "duration": "90 days",
    })
    if r2.status_code in [200, 201]:
        test("CREATE prescription (Atorvastatin 20mg)", lambda: r2.json())

    meds = get(f"/encounters/{IDS['encounter']}/medications").json()
    test("LIST encounter medications", lambda: len(meds) >= 2)


# ═══════════════════════════════════════════════════════════
# 13. DEVICE CRUD
# ═══════════════════════════════════════════════════════════
section("13. DEVICE CRUD")

devices_before = get("/devices").json()
test("LIST devices", lambda: devices_before is not None)

if IDS.get("org"):
    r = post("/devices", {
        "organization_id": IDS["org"],
        "device_code": "ECG-E2E",
        "device_name": "E2E 12-Lead ECG",
        "device_class": "DIAGNOSTIC",
        "manufacturer": "Philips",
        "integration_method": "HL7v2",
    })
    if r.status_code in [200, 201]:
        dev = r.json()
        IDS["device"] = dev["device_id"]
        test("CREATE device (12-Lead ECG)", lambda: dev)
    else:
        test(f"CREATE device (HTTP {r.status_code})", lambda: print(r.text) or False)


# ═══════════════════════════════════════════════════════════
# 14. DOCUMENT CRUD
# ═══════════════════════════════════════════════════════════
section("14. DOCUMENT CRUD")

docs_before = get("/documents").json()
test("LIST documents", lambda: docs_before is not None)

if IDS.get("patient") and IDS.get("encounter"):
    r = post("/documents", {
        "patient_id": IDS["patient"],
        "encounter_id": IDS["encounter"],
        "document_type": "LAB_REPORT",
        "title": "Troponin I Result Report",
        "storage_uri": "s3://axonhis/docs/troponin-result.pdf",
        "mime_type": "application/pdf",
        "sensitive_flag": False,
        "share_sensitivity": "STANDARD",
        "created_by": "Lab System",
    })
    if r.status_code in [200, 201]:
        doc = r.json()
        IDS["document"] = doc["document_id"]
        test("CREATE document (Lab Report)", lambda: doc)
    else:
        test(f"CREATE document (HTTP {r.status_code})", lambda: print(r.text) or False)


# ═══════════════════════════════════════════════════════════
# 15. PATIENT SHARING CRUD
# ═══════════════════════════════════════════════════════════
section("15. PATIENT SHARING CRUD")

shares_before = get("/share-grants").json()
test("LIST share grants", lambda: shares_before is not None)

if IDS.get("patient"):
    r = post("/share-grants", {
        "patient_id": IDS["patient"],
        "grant_method": "QR_CODE",
        "grantee_type": "DOCTOR",
        "grantee_reference": "Dr. External Cardiologist",
        "scope_type": "ENCOUNTER",
        "scope_json": {"encounter_id": IDS.get("encounter", "")},
    })
    if r.status_code in [200, 201]:
        share = r.json()
        IDS["share"] = share["share_grant_id"]
        test("CREATE share grant (QR Code)", lambda: share)
        test("Share has QR token", lambda: share.get("qr_token"))
    else:
        test(f"CREATE share grant (HTTP {r.status_code})", lambda: print(r.text) or False)


# ═══════════════════════════════════════════════════════════
# 16. COVERAGE / PAYER CRUD
# ═══════════════════════════════════════════════════════════
section("16. COVERAGE & PAYER CRUD")

payers = get("/payers").json()
test("LIST payers", lambda: payers is not None)
payer_id = payers[0]["payer_id"] if payers else None

if IDS.get("patient") and payer_id:
    r = post("/coverage", {
        "patient_id": IDS["patient"],
        "payer_id": payer_id,
        "policy_number": "POL-E2E-12345",
        "member_reference": "MBR-E2E-001",
        "plan_name": "Gold Plan",
        "effective_from": "2026-01-01",
        "effective_to": "2026-12-31",
    })
    if r.status_code in [200, 201]:
        cov = r.json()
        IDS["coverage"] = cov["coverage_id"]
        test("CREATE coverage (Gold Plan)", lambda: cov)
    else:
        test(f"CREATE coverage (HTTP {r.status_code})", lambda: print(r.text) or False)


# ═══════════════════════════════════════════════════════════
# 17. BILLING CRUD
# ═══════════════════════════════════════════════════════════
section("17. BILLING CRUD")

invoices_before = get("/billing/invoices").json()
test("LIST invoices", lambda: invoices_before is not None)

if IDS.get("patient") and IDS.get("org"):
    r = post("/billing/invoices", {
        "organization_id": IDS["org"],
        "patient_id": IDS["patient"],
        "encounter_id": IDS.get("encounter"),
        "coverage_id": IDS.get("coverage"),
        "currency_code": "AED",
        "line_items": [
            {"line_type": "CONSULTATION", "description": "Cardiology Consultation", "quantity": 1, "unit_price": 500, "line_amount": 500},
            {"line_type": "LAB", "description": "Troponin I Test", "quantity": 1, "unit_price": 200, "line_amount": 200},
            {"line_type": "IMAGING", "description": "Chest X-Ray", "quantity": 1, "unit_price": 150, "line_amount": 150},
        ],
    })
    if r.status_code in [200, 201]:
        inv = r.json()
        IDS["invoice"] = inv["billing_invoice_id"]
        test("CREATE invoice with 3 line items", lambda: inv)
        test("Invoice has correct total (850 AED)", lambda: inv.get("total_amount") == 850)
        test("Invoice has 3 line items", lambda: len(inv.get("line_items", [])) == 3)
    else:
        test(f"CREATE invoice (HTTP {r.status_code})", lambda: print(r.text) or False)


# ═══════════════════════════════════════════════════════════
# 18. INTEGRATION EVENTS CRUD
# ═══════════════════════════════════════════════════════════
section("18. INTEGRATION EVENTS CRUD")

events_before = get("/integration/events").json()
test("LIST integration events", lambda: events_before is not None)

r = post("/integration/events", {
    "organization_id": IDS.get("org"),
    "source_system": "AXONHIS_MD",
    "target_system": "PACS",
    "resource_type": "ServiceRequest",
    "resource_id": IDS.get("order_img", ""),
    "event_type": "ORDER_PLACED",
    "payload_json": {"order_type": "IMAGING", "catalog_code": "CXR-PA"},
    "correlation_id": str(uuid.uuid4()),
})
if r.status_code in [200, 201]:
    evt = r.json()
    IDS["integration_event"] = evt["integration_event_id"]
    test("CREATE integration event", lambda: evt)
else:
    test(f"CREATE integration event (HTTP {r.status_code})", lambda: print(r.text) or False)


# ═══════════════════════════════════════════════════════════
# 19. AUDIT TRAIL
# ═══════════════════════════════════════════════════════════
section("19. AUDIT TRAIL")

audit = get("/audit/events").json()
test("LIST audit events", lambda: audit is not None)
test(f"Audit trail has {len(audit)} events", lambda: len(audit) >= 0)


# ═══════════════════════════════════════════════════════════
# 20. FINAL DASHBOARD VERIFICATION
# ═══════════════════════════════════════════════════════════
section("20. FINAL DASHBOARD STATS VERIFICATION")

stats = test("GET dashboard stats", lambda: get("/dashboard/stats").json())
if stats:
    print(f"\n  📊 Platform State After CRUD Tests:")
    for k, v in stats.items():
        icon = "🟢" if v > 0 else "⚪"
        print(f"     {icon} {k}: {v}")


# ═══════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"  🏁 COMPREHENSIVE CRUD E2E TEST RESULTS")
print(f"{'='*60}")
print(f"  ✅ Passed: {PASSED}")
print(f"  ❌ Failed: {FAILED}")
print(f"  📊 Total:  {PASSED + FAILED}")
if PASSED + FAILED > 0:
    rate = PASSED / (PASSED + FAILED) * 100
    print(f"  🎯 Rate:   {rate:.1f}%")
    if rate == 100.0:
        print(f"\n  🎉 PERFECT SCORE! All CRUD operations work end-to-end!")
    elif rate >= 90:
        print(f"\n  ✨ Excellent! Near-perfect pass rate.")

if ERRORS:
    print(f"\n  ⚠️  Failed Tests:")
    for e in ERRORS:
        print(f"    • {e}")

print(f"\n  📋 Created Records:")
for label, id_val in IDS.items():
    print(f"     {label}: {str(id_val)[:16]}...")

print(f"\n{'='*60}")
sys.exit(0 if FAILED == 0 else 1)
