"""
AXONHIS Comprehensive System Audit — E2E API Test Suite v2
Fixed with correct API routes from OpenAPI spec analysis.
"""
import urllib.request
import urllib.error
import json
import sys
import uuid
from datetime import datetime

BASE = "http://localhost:9500/api/v1"
TOKEN = None
RESULTS = []
BUG_ID = 0

def login():
    global TOKEN
    data = json.dumps({"email": "admin@axonhis.com", "password": "Admin@123"}).encode()
    req = urllib.request.Request(f"{BASE}/auth/login", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        TOKEN = json.loads(resp.read().decode())["access_token"]
    print(f"✅ Auth: Logged in successfully.\n")

def api(method, path, body=None):
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    data_bytes = json.dumps(body).encode() if body else None
    try:
        with urllib.request.urlopen(req, data=data_bytes) as resp:
            raw = resp.read().decode()
            try: return resp.status, json.loads(raw)
            except: return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try: return e.code, json.loads(raw)
        except: return e.code, raw
    except Exception as e:
        return 0, str(e)

def test(module, name, method, path, body=None, expect_codes=None):
    global BUG_ID
    if expect_codes is None:
        expect_codes = [200, 201]
    code, data = api(method, path, body)
    passed = code in expect_codes
    icon = "✅" if passed else "❌"
    result = {"module": module, "test": name, "method": method, "path": path, "status_code": code, "passed": passed}
    if not passed:
        BUG_ID += 1
        result["bug_id"] = f"BUG-{BUG_ID:03d}"
        result["detail"] = str(data)[:200] if data else "No response"
    RESULTS.append(result)
    print(f"  {icon} [{code}] {name}")
    return code, data

def run_audit():
    login()

    # ══════════════════════════════════════════════════════════
    print("═" * 60)
    print("PHASE 1: CORE PLATFORM")
    print("═" * 60)
    test("Auth", "Login", "POST", "/auth/login", body={"email":"admin@axonhis.com","password":"Admin@123"})
    test("Auth", "Invalid Login Rejected", "POST", "/auth/login", body={"email":"x@x.x","password":"wrong"}, expect_codes=[401,403,422])
    test("Auth", "Get Current User", "GET", "/auth/me")
    test("Auth", "List Users", "GET", "/auth/users")
    test("Auth", "List Roles", "GET", "/auth/roles")
    test("Audit", "Audit Logs", "GET", "/audit")
    test("Config", "System Config", "GET", "/config")
    test("Notifications", "Notifications", "GET", "/notifications")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 2: PATIENT MANAGEMENT")
    print("═" * 60)
    test("Patients", "List Patients", "GET", "/patients/")
    code, pdata = test("Patients", "Register Patient", "POST", "/patients/", body={
        "first_name":"QA","last_name":"Audit","date_of_birth":"1990-01-15","gender":"Male",
        "blood_group":"O+","phone":"+919999999999","email":"qaaudit@test.com","address":"Test"
    })
    pid = pdata.get("id") if isinstance(pdata, dict) and code in [200,201] else None
    if pid:
        test("Patients", "Get Patient by ID", "GET", f"/patients/{pid}")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 3: SCHEDULING & APPOINTMENTS")
    print("═" * 60)
    test("Scheduling", "List Calendars", "GET", "/scheduling/calendars")
    test("Scheduling", "List Bookings", "GET", "/scheduling/bookings")
    test("Scheduling", "Scheduling Analytics", "GET", "/scheduling/analytics?from_date=2026-01-01&to_date=2026-12-31")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 4: KIOSK & QUEUE")
    print("═" * 60)
    test("Kiosk", "Departments", "GET", "/kiosk/departments")
    test("Kiosk", "Doctors (Cardiology)", "GET", "/kiosk/doctors?department=Cardiology")
    code, tdata = test("Kiosk", "Generate Token", "POST", "/kiosk/token", body={"department":"General Medicine","priority":False})
    tid = tdata.get("id") if isinstance(tdata, dict) and code in [200,201] else None
    test("Kiosk", "Live Queue", "GET", "/kiosk/queue")
    if tid:
        test("Kiosk", "Call Patient", "POST", "/kiosk/call", body={"token_id":str(tid)})
        test("Kiosk", "Complete Token", "PUT", f"/kiosk/token/{tid}/status", body={"status":"Completed"})
    test("Kiosk", "Check-In", "POST", "/kiosk/check-in", body={"identifier":"TEST-001"})
    test("Kiosk", "Book Appointment", "POST", "/kiosk/appointments", body={
        "department":"General Medicine","doctor_id":"d4f3b259-2c3f-42e5-bc0c-123456789a01",
        "patient_name":"QA Patient","mobile":"+919876543210","date":datetime.now().strftime('%Y-%m-%d'),"time_slot":"10:00 AM"
    })

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 5: ENCOUNTERS & EMR")
    print("═" * 60)
    test("Encounters", "List Encounters", "GET", "/encounters")
    if pid:
        code, enc = test("Encounters", "Create Encounter", "POST", "/encounters/", body={
            "patient_id":pid,"encounter_type":"OPD","department":"General Medicine","status":"ACTIVE"
        })

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 6: OPD MODULE")
    print("═" * 60)
    test("OPD", "Pre-Registration List", "GET", "/opd/pre-registration")
    test("OPD", "Deposits List", "GET", "/opd/deposits")
    test("OPD", "Consent Templates", "GET", "/opd/consent-templates")
    test("OPD", "Consent Documents", "GET", "/opd/consent-documents")
    test("OPD", "Proforma Bills", "GET", "/opd/proforma-bills")
    test("OPD", "Waitlist", "GET", "/opd/waitlist")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 7: SMART QUEUE & NURSING TRIAGE")
    print("═" * 60)
    test("NursingTriage", "Worklist", "GET", "/nursing-triage/worklist")
    test("NursingTriage", "Templates", "GET", "/nursing-triage/templates")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 8: DOCTOR DESK (EMR)")
    print("═" * 60)
    test("DoctorDesk", "Prescriptions", "GET", "/doctor-desk/prescriptions")
    test("DoctorDesk", "Orders", "GET", "/doctor-desk/orders")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 9: LABORATORY (LIS)")
    print("═" * 60)
    test("LIS", "Lab Orders", "GET", "/lab/orders")
    test("LIS", "Test Order Panels", "GET", "/lis-orders/panels")
    test("LIS", "Phlebotomy Worklist", "GET", "/phlebotomy/worklist")
    test("LIS", "Phlebotomy Samples", "GET", "/phlebotomy/samples")
    test("LIS", "Central Receiving Dashboard", "GET", "/central-receiving/dashboard")
    test("LIS", "Central Receiving Receipts", "GET", "/central-receiving/receipts")
    test("LIS", "Lab Processing Dashboard", "GET", "/lab-processing/dashboard")
    test("LIS", "Lab Processing Worklist", "GET", "/lab-processing/worklist")
    test("LIS", "Lab Processing Results", "GET", "/lab-processing/results")
    test("LIS", "Validation Worklist", "GET", "/validation/worklist")
    test("LIS", "Validation Metrics", "GET", "/validation/metrics")
    test("LIS", "Report List", "GET", "/reports/")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 10: RADIOLOGY (RIS)")
    print("═" * 60)
    test("RIS", "Radiology Orders", "GET", "/radiology/orders")
    test("RIS", "Radiology Reports", "GET", "/radiology/reports")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 11: DIAGNOSTIC PROCEDURES")
    print("═" * 60)
    test("Diagnostics", "Templates", "GET", "/diagnostics/templates")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 12: PHARMACY")
    print("═" * 60)
    test("Pharmacy", "Prescriptions", "GET", "/pharmacy/prescriptions")
    test("Pharmacy", "Pharmacy Sales List", "GET", "/pharmacy/sales")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 13: IPD / INPATIENT")
    print("═" * 60)
    test("IPD", "Pending Requests", "GET", "/ipd/requests/pending")
    test("IPD", "Active Admissions", "GET", "/ipd/admissions")
    test("IPD", "Nursing Worklist", "GET", "/ipd/nursing/worklist")
    test("IPD", "Doctor Worklist", "GET", "/ipd/doctor/worklist")
    test("IPD", "Dashboard Stats", "GET", "/ipd/dashboard/stats")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 14: EMERGENCY (ER)")
    print("═" * 60)
    test("ER", "ER Dashboard", "GET", "/er/dashboard")
    test("ER", "ER Encounters", "GET", "/er/encounters")
    test("ER", "ER Beds", "GET", "/er/beds")
    test("ER", "MLC Cases", "GET", "/er/mlc")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 15: WARDS & BEDS")
    print("═" * 60)
    test("Wards", "List Wards", "GET", "/wards")
    test("Wards", "List Beds", "GET", "/wards/beds")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 16: BILLING & FINANCE")
    print("═" * 60)
    test("Billing", "Billing Entries", "GET", "/billing/entries")
    test("Billing", "Insurance Claims", "GET", "/billing/insurance/claims")
    test("BillingMasters", "Service Groups", "GET", "/billing-masters/service-groups")
    test("BillingMasters", "Tariff Plans", "GET", "/billing-masters/tariff-plans")
    test("BillingMasters", "Payment Modes", "GET", "/billing-masters/payment-modes")
    test("BillingMasters", "Patient Categories", "GET", "/billing-masters/patient-categories")
    test("BillingMasters", "Insurance Providers", "GET", "/billing-masters/insurance-providers")
    test("BillingMasters", "Tax Groups", "GET", "/billing-masters/tax-groups")
    test("RCM", "RCM Daily Revenue", "GET", "/rcm-billing/analytics/daily-revenue")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 17: PROCUREMENT & INVENTORY")
    print("═" * 60)
    test("Procurement", "Vendors", "GET", "/procurement/vendors")
    test("Procurement", "Purchase Requests", "GET", "/procurement/requests")
    test("Procurement", "Purchase Orders", "GET", "/procurement/orders")
    test("Procurement", "GRNs", "GET", "/procurement/grn")
    test("Procurement", "Stores", "GET", "/procurement/utils/stores")
    test("Procurement", "Items Catalog", "GET", "/procurement/utils/items")
    test("Inventory", "Inventory Stores", "GET", "/inventory/stores")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 18: SPECIALIZED MODULES")
    print("═" * 60)
    test("BloodBank", "Blood Inventory", "GET", "/advanced/blood-bank/inventory")
    test("CSSD", "CSSD Tests", "GET", "/advanced/cssd/tests")
    test("Linen", "Categories", "GET", "/linen/categories")
    test("Linen", "Batches", "GET", "/linen/batches")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 19: SYSTEM & MONITORING")
    print("═" * 60)
    test("System", "System Health", "GET", "/system/health")
    test("System", "Error Monitoring", "GET", "/system/monitoring/errors")
    test("System", "Performance Metrics", "GET", "/system/monitoring/performance")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 20: ANALYTICS & BI")
    print("═" * 60)
    test("BI", "Realtime Dashboard", "GET", "/bi-intelligence/dashboard/realtime")
    test("BI", "Management Dashboard", "GET", "/bi-intelligence/dashboard/management")
    test("BI", "Clinical Analytics", "GET", "/bi-intelligence/analytics/clinical")
    test("BI", "Financial Analytics", "GET", "/bi-intelligence/analytics/financial")
    test("Analytics", "Clinical Metrics", "GET", "/analytics/clinical-metrics")
    test("Analytics", "Financial Metrics", "GET", "/analytics/financial-metrics")
    test("Analytics", "Executive Dashboard", "GET", "/analytics/dashboards/executive")

    # ══════════════════════════════════════════════════════════
    print(f"\n{'═' * 60}")
    print("PHASE 21: PATIENT PORTAL")
    print("═" * 60)
    test("Portal", "Portal Login", "POST", "/portal/accounts/login",
         body={"email":"test@portal.com","password":"Test@123"}, expect_codes=[200,401,404,422])
    code, port_reg = test("Portal", "Portal Register", "POST", "/portal/accounts/register",
         body={"email":f"qaport{uuid.uuid4().hex[:8]}@test.com","password":"Test@123","phone":"+919999999999","full_name":"QA Portal"},
         expect_codes=[200,201,400,409,422])
    test("Portal", "Account Profile", "GET", f"/portal/accounts/profile?patient_id={uuid.uuid4()}", expect_codes=[200,401,403,404])
    test("Portal", "Account Search", "GET", "/portal/accounts/search?query=9999999999", expect_codes=[200,404])
    
    # Appointments
    test("Portal", "List Doctors", "GET", f"/portal/appointments/doctors?patient_id={uuid.uuid4()}")
    test("Portal", "My Appointments", "GET", f"/portal/appointments/my?patient_id={uuid.uuid4()}", expect_codes=[200,401,403])
    test("Portal", "Doctor Slots", "GET", f"/portal/appointments/slots?doctor_id={uuid.uuid4()}&date=2026-05-01")
    test("Portal", "Book Appointment", "POST", "/portal/appointments/book", 
         body={"doctor_id": str(uuid.uuid4()), "date": "2026-05-01", "time": "10:00", "reason": "Test"}, 
         expect_codes=[200,201,401,403,422,400,404])
         
    # Medical Records
    test("Portal", "Lab Results", "GET", f"/portal/medical-records/lab-results?patient_id={uuid.uuid4()}", expect_codes=[200,401,403])
    test("Portal", "Prescriptions", "GET", f"/portal/medical-records/prescriptions?patient_id={uuid.uuid4()}", expect_codes=[200,401,403])
    test("Portal", "Encounters", "GET", f"/portal/medical-records/encounters?patient_id={uuid.uuid4()}", expect_codes=[200,401,403])
    test("Portal", "Documents", "GET", f"/portal/medical-records/documents?patient_id={uuid.uuid4()}", expect_codes=[200,401,403])
    
    # Teleconsultations & Payments
    test("Portal", "Teleconsultations", "GET", f"/portal/telemedicine/sessions?patient_id={uuid.uuid4()}", expect_codes=[200,401,403])
    test("Portal", "Invoices", "GET", f"/portal/billing/invoices?patient_id={uuid.uuid4()}", expect_codes=[200,401,403])

    # ══════════════════════════════════════════════════════════
    # FINAL REPORT
    # ══════════════════════════════════════════════════════════
    total = len(RESULTS)
    passed = sum(1 for r in RESULTS if r["passed"])
    failed = sum(1 for r in RESULTS if not r["passed"])

    print(f"\n\n{'═' * 60}")
    print("FINAL AUDIT SUMMARY")
    print("═" * 60)
    print(f"\n  Total Tests: {total}")
    print(f"  ✅ Passed:   {passed}")
    print(f"  ❌ Failed:   {failed}")
    print(f"  Pass Rate:   {passed/total*100:.1f}%\n")

    if failed > 0:
        print("─" * 60)
        print("BUG REPORT — FAILING ENDPOINTS")
        print("─" * 60)
        for r in RESULTS:
            if not r["passed"]:
                sev = "CRITICAL" if r["status_code"] == 500 else ("MAJOR" if r["status_code"] in [404,405] else "MINOR")
                print(f"\n  🐛 {r.get('bug_id','?')} [{sev}] {r['module']} → {r['test']}")
                print(f"     {r['method']} {r['path']} → HTTP {r['status_code']}")
                if r.get("detail"):
                    print(f"     Detail: {r['detail'][:120]}")

    with open("audit_results_v2.json", "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "summary": {"total": total, "passed": passed, "failed": failed}, "results": RESULTS}, f, indent=2, default=str)

    print(f"\n📄 Full JSON report: audit_results_v2.json")
    return failed

if __name__ == "__main__":
    failures = run_audit()
    sys.exit(1 if failures else 0)
