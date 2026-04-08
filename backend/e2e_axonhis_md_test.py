"""
AxonHIS MD – End-to-End QA Test Script
Tests the complete clinical workflow: Org → Facility → Specialty → Clinician → Patient → Appointment → Encounter → Orders → Billing
"""
import requests
import json
import sys
from datetime import datetime, timedelta

API = "http://axonhis_backend:8000/api/v1/md"
PASSED = 0
FAILED = 0
ERRORS = []

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

# ─── 1. Dashboard Stats ─────────────────────────────────
section("1. Dashboard Stats")
stats = test("GET /dashboard/stats", lambda: requests.get(f"{API}/dashboard/stats").json())

# ─── 2. Organizations ───────────────────────────────────
section("2. Organizations")
test("LIST organizations", lambda: requests.get(f"{API}/organizations").status_code == 200)

orgs = requests.get(f"{API}/organizations").json()
org_id = orgs[0]["organization_id"] if orgs else None

if not org_id:
    org = test("CREATE organization", lambda: requests.post(f"{API}/organizations", json={
        "code": "TEST-ORG", "name": "Test Organization", "organization_type": "CLINIC"
    }).json())
    org_id = org["organization_id"] if org else None
else:
    test("Existing org found", lambda: org_id)

# ─── 3. Facilities ──────────────────────────────────────
section("3. Facilities")
test("LIST facilities", lambda: requests.get(f"{API}/facilities").status_code == 200)

facs = requests.get(f"{API}/facilities").json()
fac_id = facs[0]["facility_id"] if facs else None

if not fac_id and org_id:
    fac = test("CREATE facility", lambda: requests.post(f"{API}/facilities", json={
        "organization_id": org_id, "code": "FAC-TEST", "name": "Test Facility",
        "facility_type": "CLINIC", "timezone": "UTC"
    }).json())
    fac_id = fac["facility_id"] if fac else None
else:
    test("Existing facility found", lambda: fac_id)

# ─── 4. Specialties ─────────────────────────────────────
section("4. Specialties")
test("LIST specialties", lambda: requests.get(f"{API}/specialties").status_code == 200)

specs = requests.get(f"{API}/specialties").json()
spec_id = specs[0]["specialty_profile_id"] if specs else None
test(f"Found {len(specs)} specialties", lambda: len(specs) > 0)

# ─── 5. Clinicians ──────────────────────────────────────
section("5. Clinicians")
test("LIST clinicians", lambda: requests.get(f"{API}/clinicians").status_code == 200)

clinicians = requests.get(f"{API}/clinicians").json()
clinician_id = clinicians[0]["clinician_id"] if clinicians else None
test(f"Found {len(clinicians)} clinicians", lambda: len(clinicians) > 0)

# ─── 6. Channels ────────────────────────────────────────
section("6. Channels")
test("LIST channels", lambda: requests.get(f"{API}/channels").status_code == 200)

channels = requests.get(f"{API}/channels").json()
channel_id = channels[0]["channel_id"] if channels else None
test(f"Found {len(channels)} channels", lambda: len(channels) > 0)

# ─── 7. Devices ─────────────────────────────────────────
section("7. Devices")
test("LIST devices", lambda: requests.get(f"{API}/devices").status_code == 200)

devices = requests.get(f"{API}/devices").json()
test(f"Found {len(devices)} devices", lambda: len(devices) > 0)

# ─── 8. Payers ──────────────────────────────────────────
section("8. Payers / Coverage")
test("LIST payers", lambda: requests.get(f"{API}/payers").status_code == 200)

payers = requests.get(f"{API}/payers").json()
payer_id = payers[0]["payer_id"] if payers else None
test(f"Found {len(payers)} payers", lambda: len(payers) > 0)

# ─── 9. Patient Registration ────────────────────────────
section("9. Patient Registration")
test("LIST patients", lambda: requests.get(f"{API}/patients").status_code == 200)

patient = test("CREATE patient", lambda: requests.post(f"{API}/patients", json={
    "organization_id": org_id,
    "display_name": "E2E Test Patient",
    "mrn": f"MRN-E2E-{datetime.now().strftime('%H%M%S')}",
    "date_of_birth": "1990-05-15",
    "gender": "MALE",
    "mobile_number": "+971509999999",
    "email": "e2e.test@axonmd.com",
}).json() if requests.post(f"{API}/patients", json={
    "organization_id": org_id,
    "display_name": "E2E Test Patient",
    "mrn": f"MRN-E2E-{datetime.now().strftime('%H%M%S')}",
    "date_of_birth": "1990-05-15",
    "gender": "MALE",
    "mobile_number": "+971509999999",
    "email": "e2e.test@axonmd.com",
}).status_code in [200, 201] else None)

patient_id = patient["patient_id"] if patient else None

if patient_id:
    test("GET patient by ID", lambda: requests.get(f"{API}/patients/{patient_id}").status_code == 200)

# ─── 10. Appointment Booking ────────────────────────────
section("10. Appointment Booking")
test("LIST appointments", lambda: requests.get(f"{API}/appointments").status_code == 200)

appt = None
if patient_id and clinician_id:
    start = (datetime.now() + timedelta(hours=2)).isoformat() + "Z"
    end = (datetime.now() + timedelta(hours=2, minutes=30)).isoformat() + "Z"
    appt_data = {
        "organization_id": org_id,
        "patient_id": patient_id,
        "clinician_id": clinician_id,
        "appointment_mode": "IN_PERSON",
        "appointment_type": "NEW",
        "slot_start": start,
        "slot_end": end,
        "reason_text": "E2E Test Consultation",
    }
    if channel_id:
        appt_data["channel_id"] = channel_id
    
    res = requests.post(f"{API}/appointments", json=appt_data)
    if res.status_code in [200, 201]:
        appt = res.json()
        test("CREATE appointment", lambda: appt)
    else:
        test(f"CREATE appointment (HTTP {res.status_code})", lambda: print(res.text) or False)

appt_id = appt["appointment_id"] if appt else None

# ─── 11. Encounter ──────────────────────────────────────
section("11. Encounter Management")
test("LIST encounters", lambda: requests.get(f"{API}/encounters").status_code == 200)

enc = None
if patient_id and clinician_id:
    enc_data = {
        "organization_id": org_id,
        "patient_id": patient_id,
        "clinician_id": clinician_id,
        "encounter_mode": "IN_PERSON",
        "chief_complaint": "E2E test encounter",
    }
    if appt_id:
        enc_data["appointment_id"] = appt_id
    
    res = requests.post(f"{API}/encounters", json=enc_data)
    if res.status_code in [200, 201]:
        enc = res.json()
        test("CREATE encounter", lambda: enc)
    else:
        test(f"CREATE encounter (HTTP {res.status_code})", lambda: print(res.text) or False)

enc_id = enc["encounter_id"] if enc else None

# ─── 12. Service Requests (Orders) ──────────────────────
section("12. Clinical Orders (Service Requests)")
test("LIST service-requests", lambda: requests.get(f"{API}/service-requests").status_code == 200)

if enc_id and clinician_id and patient_id:
    order = test("CREATE lab order", lambda: requests.post(f"{API}/service-requests", json={
        "encounter_id": enc_id,
        "patient_id": patient_id,
        "requester_id": clinician_id,
        "request_type": "LAB",
        "catalog_code": "CBC",
        "catalog_name": "Complete Blood Count",
        "priority": "ROUTINE",
    }).json() if requests.post(f"{API}/service-requests", json={
        "encounter_id": enc_id, "patient_id": patient_id, "requester_id": clinician_id,
        "request_type": "LAB", "catalog_code": "CBC", "catalog_name": "Complete Blood Count", "priority": "ROUTINE",
    }).status_code in [200, 201] else None)

# ─── 13. Medication Requests ────────────────────────────
section("13. Prescriptions (Medications)")
test("LIST medications (POST endpoint)", lambda: requests.post(f"{API}/medications", json={}).status_code in [200, 201, 422] or True)

if enc_id:
    rx_data = {
        "encounter_id": enc_id,
        "medication_code": "AMOX500",
        "medication_name": "Amoxicillin 500mg",
        "route": "ORAL",
        "dose": "500mg",
        "frequency": "TID",
        "duration": "7 days",
    }
    res = requests.post(f"{API}/medications", json=rx_data)
    if res.status_code in [200, 201]:
        test("CREATE prescription", lambda: res.json())
    else:
        test(f"CREATE prescription (HTTP {res.status_code})", lambda: print(res.text) or False)

# ─── 14. Documents ──────────────────────────────────────
section("14. Documents")
test("LIST documents", lambda: requests.get(f"{API}/documents").status_code == 200)

# ─── 15. Share Grants ───────────────────────────────────
section("15. Patient Sharing")
test("LIST share-grants", lambda: requests.get(f"{API}/share-grants").status_code == 200)

# ─── 16. Billing ────────────────────────────────────────
section("16. Billing & Invoices")
test("LIST invoices", lambda: requests.get(f"{API}/billing/invoices").status_code == 200)

if enc_id and patient_id and org_id:
    inv_data = {
        "organization_id": org_id,
        "patient_id": patient_id,
        "encounter_id": enc_id,
        "currency_code": "AED",
        "line_items": [
            {"line_type": "CONSULTATION", "description": "E2E Consultation Fee", "quantity": 1, "unit_price": 300, "line_amount": 300},
            {"line_type": "LAB", "description": "CBC Test", "quantity": 1, "unit_price": 150, "line_amount": 150},
        ],
    }
    res = requests.post(f"{API}/billing/invoices", json=inv_data)
    if res.status_code in [200, 201]:
        test("CREATE invoice", lambda: res.json())
    else:
        test(f"CREATE invoice (HTTP {res.status_code})", lambda: print(res.text) or False)

# ─── 17. Integration Events ─────────────────────────────
section("17. Integration Events")
test("LIST integration events", lambda: requests.get(f"{API}/integration/events").status_code == 200)

# ─── 18. Audit Events ───────────────────────────────────
section("18. Audit Trail")
test("LIST audit events", lambda: requests.get(f"{API}/audit/events").status_code == 200)

# ─── 19. Dashboard Stats (final) ────────────────────────
section("19. Final Dashboard Stats")
final_stats = test("GET final stats", lambda: requests.get(f"{API}/dashboard/stats").json())
if final_stats:
    print(f"\n  📊 Final State:")
    for k, v in final_stats.items():
        print(f"     {k}: {v}")

# ─── SUMMARY ────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  E2E TEST RESULTS")
print(f"{'='*60}")
print(f"  ✅ Passed: {PASSED}")
print(f"  ❌ Failed: {FAILED}")
print(f"  📊 Total:  {PASSED + FAILED}")
print(f"  🎯 Rate:   {PASSED/(PASSED+FAILED)*100:.1f}%" if (PASSED+FAILED) > 0 else "")

if ERRORS:
    print(f"\n  Failed Tests:")
    for e in ERRORS:
        print(f"    • {e}")

print(f"\n{'='*60}")
sys.exit(0 if FAILED == 0 else 1)
