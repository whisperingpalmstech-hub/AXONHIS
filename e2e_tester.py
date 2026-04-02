import json
import urllib.request
import urllib.error
import uuid
import sys
from datetime import datetime, timedelta

# Configuration
API_BASE = "http://localhost:9500/api/v1"
HEADERS = {"Content-Type": "application/json"}

# Sensible Dummy Data
DUMMY_PATIENT = {
    "first_name": "James",
    "last_name": "Miller",
    "date_of_birth": "1985-06-15",
    "gender": "male",
    "primary_phone": "+1234567890",
    "email": f"james.miller.{uuid.uuid4().hex[:6]}@example.com",
    "address": "123 Healthcare Ave, Medical City",
    "blood_group": "O+",
    "emergency_contact_name": "Sarah Miller",
    "emergency_contact_phone": "+1987654321"
}

def make_request(method, url, data=None, headers=None):
    if headers is None:
        headers = {}
    
    req_data = None
    if data:
        req_data = json.dumps(data).encode('utf-8')
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return e.code, body
    except Exception as e:
        return 500, str(e)

def log(msg):
    print(msg)
    sys.stdout.flush()

def run_e2e_tests():
    log("="*60)
    log("🚀 AXONHIS ENTERPRISE E2E AUTOMATED TEST SUITE")
    log("="*60)
    
    # ─────────────────────────────────────────────────────────────
    # 0. CORE: AUTHENTICATE AS ADMIN (TO CREATE PATIENTS)
    # ─────────────────────────────────────────────────────────────
    log("\n[0] Authenticating as Hospital Admin...")
    admin_cred = {"email": "admin@axonhis.com", "password": "Admin@123"}
    status, res = make_request("POST", f"{API_BASE}/auth/login", data=admin_cred, headers=HEADERS)
    
    if status == 200 and type(res) == dict and "access_token" in res:
        admin_token = res["access_token"]
        log("✅ Admin Authentication Successful!")
    else:
        log(f"❌ Admin Authentication Failed (Status {status}): {res}")
        return

    admin_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}"
    }

    # Fetch admin ID (to use as doctor_id in booking)
    status, res = make_request("GET", f"{API_BASE}/auth/me", headers=admin_headers)
    admin_id = res['id'] if status == 200 else None
    if admin_id:
        log(f"✅ Found Doc/Admin ID for booking: {admin_id}")
    else:
        log("⚠️ Could not fetch Admin ID, booking test may fail.")

    # ─────────────────────────────────────────────────────────────
    # 1. CORE: PATIENT REGISTRATION
    # ─────────────────────────────────────────────────────────────
    log("\n[1] Registering New Patient in Main HIS...")
    status, res = make_request("POST", f"{API_BASE}/patients/", data=DUMMY_PATIENT, headers=admin_headers)
    if status not in (200, 201):
        log(f"❌ Failed to register patient (Status {status}): {res}")
        return
        
    patient_id = res["id"]
    log(f"✅ Patient Registered Successfully! ID: {patient_id}")
    
    # ─────────────────────────────────────────────────────────────
    # 2. PATIENT PORTAL: SEARCH RECORDS
    # ─────────────────────────────────────────────────────────────
    log("\n[2] Patient Portal: Searching for records by Email...")
    portal_search_url = f"{API_BASE}/portal/accounts/search?query={DUMMY_PATIENT['email']}"
    status, res = make_request("GET", portal_search_url, headers=HEADERS)
    
    if status == 200 and type(res) == dict and res.get("patient_id") == patient_id:
        log("✅ Portal Search Successful! Found matching core record.")
    else:
        log(f"❌ Portal Search Failed (Status {status}): {res}")
        return

    # ─────────────────────────────────────────────────────────────
    # 3. PATIENT PORTAL: ACCOUNT CREATION (REGISTRATION)
    # ─────────────────────────────────────────────────────────────
    log("\n[3] Patient Portal: Creating Portal Login Credentials...")
    portal_cred = {
        "email": DUMMY_PATIENT["email"],
        "password": "SecurePassword123!",
        "patient_id": patient_id
    }
    status, res = make_request("POST", f"{API_BASE}/portal/accounts/register", data=portal_cred, headers=HEADERS)
    if status in (200, 201):
        log("✅ Portal Account Linked & Created Successfully!")
    else:
        log(f"❌ Portal Account Creation Failed (Status {status}): {res}")
        return

    # ─────────────────────────────────────────────────────────────
    # 4. PATIENT PORTAL: LOGIN
    # ─────────────────────────────────────────────────────────────
    log("\n[4] Patient Portal: Executing Secure Login...")
    login_cred = {
        "email": portal_cred["email"],
        "password": portal_cred["password"]
    }
    status, res = make_request("POST", f"{API_BASE}/portal/accounts/login", data=login_cred, headers=HEADERS)
    
    if status == 200 and type(res) == dict and "access_token" in res:
        token = res["access_token"]
        log("✅ Patient Login Successful! JWT Token acquired.")
    else:
        log(f"❌ Portal Login Failed (Status {status}): {res}")
        return

    portal_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # ─────────────────────────────────────────────────────────────
    # 5. PATIENT PORTAL: FETCH MEDICAL RECORD AGGREGATION
    # ─────────────────────────────────────────────────────────────
    log("\n[5] Patient Portal: Fetching Encounters & Profile...")
    profile_url = f"{API_BASE}/portal/accounts/profile?patient_id={patient_id}"
    status, res = make_request("GET", profile_url, headers=portal_headers)
    if status == 200:
        log(f"✅ Profile Fetched Data Name: {res.get('first_name')}")
    else:
        log(f"❌ Failed to fetch profile (Status {status}): {res}")
        
    # Corrected path for encounters
    enc_url = f"{API_BASE}/portal/medical-records/encounters?patient_id={patient_id}"
    status, res = make_request("GET", enc_url, headers=portal_headers)
    if status == 200:
        log(f"✅ Encounter History successfully retrieved: {len(res)} records found.")
    else:
        log(f"❌ Failed to fetch encounters (Status {status}): {res}")

    # ─────────────────────────────────────────────────────────────
    # 6. SCHEDULING: BOOK APPOINTMENT
    # ─────────────────────────────────────────────────────────────
    log("\n[6] Cross-Module Integration: Booking OPD Appointment via Portal")
    if not admin_id:
        log("❌ Skipping booking because no valid doctor_id was found.")
    else:
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
        params = f"patient_id={patient_id}&doctor_id={admin_id}&appointment_time={tomorrow}&type=in_person&reason=Routine+Annual+Checkup"
        book_url = f"{API_BASE}/portal/appointments/book?{params}"
        status, res = make_request("POST", book_url, headers=portal_headers)
        
        if status == 200:
            log("✅ Appointment successfully injected into Master Scheduling Engine!")
        else:
            log(f"❌ Appointment Booking Failed (Status {status}): {res}")

    log("\n" + "="*60)
    log("🎯 END TO END AUTOMATED TEST SUITE COMPLETED")
    log("="*60)

if __name__ == "__main__":
    run_e2e_tests()
