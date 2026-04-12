#!/usr/bin/env python3
"""
End-to-End Backend API Test
Tests complete patient journey using a single ID
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:9500/api/v1"
BASE_URL = "http://localhost:9500"
LOGIN_EMAIL = "admin@axonhis.com"
LOGIN_PASSWORD = "Admin@123"

# Test Results
test_results = []
test_data = {}

def log_test(step: str, status: str, message: str = ""):
    """Log test result"""
    result = {
        "step": step,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    status_icon = "✅" if status == "PASS" else "❌"
    print(f"{status_icon} {step:40} - {message}")

def get_auth_token() -> str:
    """Get authentication token"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD}
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            log_test("Authentication", "PASS", "Login successful")
            return token
        else:
            log_test("Authentication", "FAIL", f"Status {response.status_code}")
            return None
    except Exception as e:
        log_test("Authentication", "FAIL", str(e))
        return None

def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            log_test("Health Check", "PASS", "System is healthy")
            return True
        else:
            log_test("Health Check", "FAIL", f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Health Check", "FAIL", str(e))
        return False

def create_patient(token: str) -> str:
    """Create a test patient"""
    patient_data = {
        "first_name": "Test",
        "last_name": "Patient",
        "date_of_birth": "1990-01-01",
        "gender": "Male",
        "blood_group": "O+",
        "contact_number": "9876543210",
        "email": f"test.patient.{uuid.uuid4().hex[:8]}@example.com",
        "address": "123 Test Street, Test City",
        "emergency_contact_name": "Emergency Contact",
        "emergency_contact_number": "9876543211"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/patients",
            headers={"Authorization": f"Bearer {token}"},
            json=patient_data,
            timeout=10
        )
        if response.status_code in [200, 201]:
            patient_id = response.json().get("id") or response.json().get("uhid")
            log_test("Create Patient", "PASS", f"Patient created with ID: {patient_id}")
            test_data["patient_id"] = patient_id
            return patient_id
        else:
            log_test("Create Patient", "FAIL", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        log_test("Create Patient", "FAIL", str(e))
        return None

def get_patient(token: str, patient_id: str) -> bool:
    """Get patient details"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/patients/{patient_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            log_test("Get Patient", "PASS", f"Retrieved patient {patient_id}")
            return True
        else:
            log_test("Get Patient", "FAIL", f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Get Patient", "FAIL", str(e))
        return False

def create_ipd_admission_request(token: str, patient_id: str) -> str:
    """Create IPD admission request"""
    admission_data = {
        "patient_name": "Test Patient",
        "patient_uhid": str(patient_id),
        "gender": "Male",
        "date_of_birth": "1990-01-01",
        "mobile_number": "9876543210",
        "treating_doctor": "Dr. Smith",
        "specialty": "General Medicine",
        "reason_for_admission": "Test admission for end-to-end testing",
        "admission_category": "Emergency",
        "admission_source": "ER",
        "preferred_bed_category": "General Ward",
        "expected_admission_date": datetime.now().isoformat(),
        "admitting_doctor": "Dr. Smith"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ipd/requests",
            headers={"Authorization": f"Bearer {token}"},
            json=admission_data,
            timeout=10
        )
        if response.status_code in [200, 201]:
            admission_number = response.json().get("admission_number")
            log_test("Create IPD Request", "PASS", f"Admission request created: {admission_number}")
            test_data["admission_number"] = admission_number
            return admission_number
        else:
            log_test("Create IPD Request", "FAIL", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        log_test("Create IPD Request", "FAIL", str(e))
        return None

def get_ipd_admissions(token: str) -> bool:
    """Get IPD admissions list"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/ipd/admissions",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            log_test("Get IPD Admissions", "PASS", "Retrieved admissions list")
            return True
        else:
            log_test("Get IPD Admissions", "FAIL", f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Get IPD Admissions", "FAIL", str(e))
        return False

def create_diet_prescription(token: str, admission_number: str) -> bool:
    """Create diet prescription"""
    diet_data = {
        "diet_type": "Standard Routine",
        "meal_instructions": "No special instructions for testing",
        "allergies": "NKDA"
    }
    
    try:
        response = requests.put(
            f"{API_BASE_URL}/ipd/diet/{admission_number}",
            headers={"Authorization": f"Bearer {token}"},
            json=diet_data,
            timeout=10
        )
        if response.status_code == 200:
            log_test("Create Diet Prescription", "PASS", f"Diet prescription created for {admission_number}")
            return True
        else:
            log_test("Create Diet Prescription", "FAIL", f"Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test("Create Diet Prescription", "FAIL", str(e))
        return False

def get_diet_prescription(token: str, admission_number: str) -> bool:
    """Get diet prescription"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/ipd/diet/{admission_number}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            log_test("Get Diet Prescription", "PASS", f"Retrieved diet for {admission_number}")
            return True
        else:
            log_test("Get Diet Prescription", "FAIL", f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Get Diet Prescription", "FAIL", str(e))
        return False

def create_vitals(token: str, admission_number: str) -> bool:
    """Create patient vitals"""
    vitals_data = {
        "temperature": 98.6,
        "pulse": 72,
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "respiratory_rate": 16,
        "spo2": 98,
        "recorded_by": "Test Nurse"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ipd/vitals/{admission_number}",
            headers={"Authorization": f"Bearer {token}"},
            json=vitals_data,
            timeout=10
        )
        if response.status_code == 200:
            log_test("Create Vitals", "PASS", f"Vitals recorded for {admission_number}")
            return True
        else:
            log_test("Create Vitals", "FAIL", f"Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test("Create Vitals", "FAIL", str(e))
        return False

def get_discharge_state(token: str, admission_number: str) -> bool:
    """Get discharge state"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/ipd/discharge/{admission_number}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            log_test("Get Discharge State", "PASS", f"Retrieved discharge state for {admission_number}")
            return True
        else:
            log_test("Get Discharge State", "FAIL", f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Get Discharge State", "FAIL", str(e))
        return False

def generate_discharge_summary(token: str, admission_number: str) -> bool:
    """Generate discharge summary"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/ipd/discharge/{admission_number}/summary/generate",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            log_test("Generate Discharge Summary", "PASS", f"Summary generated for {admission_number}")
            return True
        else:
            log_test("Generate Discharge Summary", "FAIL", f"Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test("Generate Discharge Summary", "FAIL", str(e))
        return False

def create_ot_room(token: str) -> str:
    """Create OT room"""
    ot_room_data = {
        "room_code": f"OT-{uuid.uuid4().hex[:4].upper()}",
        "room_name": "Test OT Room for E2E",
        "room_type": "general",
        "is_laminar_flow": True,
        "has_c_arm": True,
        "has_laser": False
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/ot-enhanced/rooms",
            headers={"Authorization": f"Bearer {token}"},
            json=ot_room_data,
            timeout=10
        )
        if response.status_code == 200:
            room_id = response.json().get("id")
            log_test("Create OT Room", "PASS", f"OT room created with ID: {room_id}")
            test_data["ot_room_id"] = room_id
            return room_id
        else:
            log_test("Create OT Room", "FAIL", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        log_test("Create OT Room", "FAIL", str(e))
        return None

def get_ot_dashboard(token: str) -> bool:
    """Get OT dashboard"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/ot-enhanced/dashboard",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            log_test("Get OT Dashboard", "PASS", "Retrieved OT dashboard stats")
            return True
        else:
            log_test("Get OT Dashboard", "FAIL", f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Get OT Dashboard", "FAIL", str(e))
        return False

def get_lab_dashboard(token: str) -> bool:
    """Get Lab dashboard"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/lab/dashboard/stats",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            log_test("Get Lab Dashboard", "PASS", "Retrieved lab dashboard stats")
            return True
        else:
            log_test("Get Lab Dashboard", "FAIL", f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Get Lab Dashboard", "FAIL", str(e))
        return False

def get_opd_pre_registration(token: str) -> bool:
    """Get OPD pre-registration"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/opd/pre-registration",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        if response.status_code == 200:
            log_test("Get OPD Pre-Registration", "PASS", "Retrieved OPD pre-registration list")
            return True
        else:
            log_test("Get OPD Pre-Registration", "FAIL", f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Get OPD Pre-Registration", "FAIL", str(e))
        return False

def run_end_to_end_test():
    """Run complete end-to-end test"""
    print("=" * 80)
    print("END-TO-END BACKEND API TEST")
    print("Testing complete patient journey using single ID")
    print("=" * 80)
    
    # Step 1: Authentication
    print("\n[1/15] Authentication...")
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed. Cannot proceed.")
        return
    
    # Step 2: Health Check
    print("\n[2/15] Health Check...")
    test_health_check()
    
    # Step 3: Create Patient
    print("\n[3/15] Create Patient...")
    patient_id = create_patient(token)
    if not patient_id:
        print("❌ Patient creation failed. Cannot proceed with patient-dependent tests.")
        # Continue with non-patient dependent tests
    
    # Step 4: Get Patient
    if patient_id:
        print("\n[4/15] Get Patient...")
        get_patient(token, patient_id)
    
    # Step 5: Create IPD Admission Request
    admission_number = None
    if patient_id:
        print("\n[5/15] Create IPD Admission Request...")
        admission_number = create_ipd_admission_request(token, patient_id)
    
    # Step 6: Get IPD Admissions
    print("\n[6/15] Get IPD Admissions...")
    get_ipd_admissions(token)
    
    # Step 7: Create Diet Prescription
    if admission_number:
        print("\n[7/15] Create Diet Prescription...")
        create_diet_prescription(token, admission_number)
    
    # Step 8: Get Diet Prescription
    if admission_number:
        print("\n[8/15] Get Diet Prescription...")
        get_diet_prescription(token, admission_number)
    
    # Step 9: Create Vitals
    if admission_number:
        print("\n[9/15] Create Vitals...")
        create_vitals(token, admission_number)
    
    # Step 10: Get Discharge State
    if admission_number:
        print("\n[10/15] Get Discharge State...")
        get_discharge_state(token, admission_number)
    
    # Step 11: Generate Discharge Summary
    if admission_number:
        print("\n[11/15] Generate Discharge Summary...")
        generate_discharge_summary(token, admission_number)
    
    # Step 12: Create OT Room
    print("\n[12/15] Create OT Room...")
    create_ot_room(token)
    
    # Step 13: Get OT Dashboard
    print("\n[13/15] Get OT Dashboard...")
    get_ot_dashboard(token)
    
    # Step 14: Get Lab Dashboard
    print("\n[14/15] Get Lab Dashboard...")
    get_lab_dashboard(token)
    
    # Step 15: Get OPD Pre-Registration
    print("\n[15/15] Get OPD Pre-Registration...")
    get_opd_pre_registration(token)
    
    # Print Summary
    print("\n" + "=" * 80)
    print("END-TO-END TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    total = len(test_results)
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    if total > 0:
        print(f"Success Rate: {(passed/total*100):.1f}%")
    
    print(f"\nTest Data:")
    print(f"  Patient ID: {test_data.get('patient_id', 'N/A')}")
    print(f"  Admission Number: {test_data.get('admission_number', 'N/A')}")
    print(f"  OT Room ID: {test_data.get('ot_room_id', 'N/A')}")
    
    if failed > 0:
        print("\nFailed Tests:")
        for r in test_results:
            if r["status"] == "FAIL":
                print(f"  - {r['step']:40} - {r['message']}")
    
    # Save results to file
    with open("/home/sujeetnew/Downloads/AXONHIS/backend/e2e_test_results.json", "w") as f:
        json.dump({
            "test_results": test_results,
            "test_data": test_data
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: e2e_test_results.json")
    print("=" * 80)

if __name__ == "__main__":
    run_end_to_end_test()
