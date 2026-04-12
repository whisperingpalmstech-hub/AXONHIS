#!/usr/bin/env python3
"""
Comprehensive Backend API Test Script
Tests all major endpoints with smart dummy data
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Configuration
API_BASE_URL = "http://localhost:9500/api/v1"
BASE_URL = "http://localhost:9500"
LOGIN_EMAIL = "admin@axonhis.com"
LOGIN_PASSWORD = "Admin@123"

# Test Results
test_results = []

def log_test(endpoint: str, method: str, status: str, message: str = ""):
    """Log test result"""
    result = {
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    status_icon = "✅" if status == "PASS" else "❌"
    print(f"{status_icon} {method} {endpoint} - {message}")

def get_auth_token() -> str:
    """Get authentication token"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD}
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            log_test("/auth/login", "POST", "PASS", "Authentication successful")
            return token
        else:
            log_test("/auth/login", "POST", "FAIL", f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        log_test("/auth/login", "POST", "FAIL", str(e))
        return None

def test_endpoint(endpoint: str, method: str, token: str = None, data: Dict = None, params: Dict = None, use_root: bool = False) -> requests.Response:
    """Test a single endpoint"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    base = BASE_URL if use_root else API_BASE_URL
    
    try:
        if method == "GET":
            response = requests.get(f"{base}{endpoint}", headers=headers, params=params)
        elif method == "POST":
            response = requests.post(f"{base}{endpoint}", headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(f"{base}{endpoint}", headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(f"{base}{endpoint}", headers=headers)
        
        if response.status_code in [200, 201]:
            log_test(endpoint, method, "PASS", f"Status {response.status_code}")
        else:
            log_test(endpoint, method, "FAIL", f"Status {response.status_code}: {response.text[:200]}")
        
        return response
    except Exception as e:
        log_test(endpoint, method, "FAIL", str(e))
        return None

def generate_dummy_patient() -> Dict:
    """Generate dummy patient data"""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "gender": "Male",
        "blood_group": "O+",
        "contact_number": "9876543210",
        "email": f"john.doe.{uuid.uuid4().hex[:8]}@example.com",
        "address": "123 Main St, City",
        "emergency_contact_name": "Jane Doe",
        "emergency_contact_number": "9876543211"
    }

def generate_dummy_admission() -> Dict:
    """Generate dummy admission data"""
    return {
        "patient_name": "John Doe",
        "patient_uhid": "UHID-TEST-001",
        "gender": "Male",
        "date_of_birth": "1990-01-01",
        "mobile_number": "9876543210",
        "treating_doctor": "Dr. Smith",
        "specialty": "General Medicine",
        "reason_for_admission": "Fever and cough",
        "admission_category": "Emergency",
        "admission_source": "ER",
        "preferred_bed_category": "General Ward",
        "expected_admission_date": datetime.now().isoformat(),
        "admitting_doctor": "Dr. Smith"
    }

def run_all_tests():
    """Run all endpoint tests"""
    print("=" * 80)
    print("BACKEND API ENDPOINT TESTING")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Testing with: {LOGIN_EMAIL}")
    print("=" * 80)
    
    # Get authentication token
    print("\n[1/10] Testing Authentication...")
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed. Cannot proceed with tests.")
        return
    
    # Test Health Check
    print("\n[2/10] Testing Health Check...")
    test_endpoint("/health", "GET", None, use_root=True)  # Public endpoint, no auth needed
    test_endpoint("/health/readiness", "GET", None, use_root=True)  # Public endpoint
    test_endpoint("/health/liveness", "GET", None, use_root=True)  # Public endpoint
    
    # Test Patient Endpoints
    print("\n[3/10] Testing Patient Endpoints...")
    test_endpoint("/patients", "GET", token)
    
    # Create a test patient
    patient_data = generate_dummy_patient()
    patient_response = test_endpoint("/patients", "POST", token, patient_data)
    patient_id = None
    if patient_response and patient_response.status_code in [200, 201]:
        patient_id = patient_response.json().get("id") or patient_response.json().get("uhid")
        if patient_id:
            print(f"   Created patient with ID: {patient_id}")
            test_endpoint(f"/patients/{patient_id}", "GET", token)
    
    # Test IPD Endpoints
    print("\n[4/10] Testing IPD Endpoints...")
    test_endpoint("/ipd/admissions", "GET", token)
    
    # Create test admission request
    admission_data = generate_dummy_admission()
    if patient_id:
        admission_data["patient_uhid"] = str(patient_id)
    
    admission_response = test_endpoint("/ipd/requests", "POST", token, admission_data)
    admission_number = None
    if admission_response and admission_response.status_code in [200, 201]:
        admission_number = admission_response.json().get("admission_number")
        if admission_number:
            print(f"   Created admission with number: {admission_number}")
            test_endpoint(f"/ipd/admissions/{admission_number}", "GET", token)
            
            # Test Diet Prescription
            print("\n[5/10] Testing Diet Prescription Endpoints...")
            diet_data = {
                "diet_type": "Standard Routine",
                "meal_instructions": "No special instructions",
                "allergies": "NKDA"
            }
            test_endpoint(f"/ipd/diet/{admission_number}", "PUT", token, diet_data)
            test_endpoint(f"/ipd/diet/{admission_number}", "GET", token)
            
            # Test Discharge Endpoints
            print("\n[6/10] Testing Discharge Endpoints...")
            test_endpoint(f"/ipd/discharge/{admission_number}", "GET", token)
            test_endpoint(f"/ipd/discharge/{admission_number}/pending-orders", "GET", token)
            test_endpoint(f"/ipd/discharge/{admission_number}/summary/generate", "POST", token)
            
            # Test Vitals
            print("\n[7/10] Testing Vitals Endpoints...")
            vitals_data = {
                "temperature": 98.6,
                "pulse": 72,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "respiratory_rate": 16,
                "spo2": 98,
                "recorded_by": "Nurse"
            }
            test_endpoint(f"/ipd/vitals/{admission_number}", "POST", token, vitals_data)
    
    # Test OPD Endpoints
    print("\n[8/10] Testing OPD Endpoints...")
    test_endpoint("/opd/pre-registration", "GET", token)
    
    # Test OT Endpoints
    print("\n[9/10] Testing OT Endpoints...")
    test_endpoint("/ot-enhanced/dashboard", "GET", token)
    test_endpoint("/ot-enhanced/rooms", "GET", token)
    
    ot_room_data = {
        "room_code": f"OT-{uuid.uuid4().hex[:4].upper()}",
        "room_name": "Test OT Room",
        "room_type": "general",
        "is_laminar_flow": True,
        "has_c_arm": True,
        "has_laser": False
    }
    test_endpoint("/ot-enhanced/rooms", "POST", token, ot_room_data)
    
    # Test Lab Endpoints
    print("\n[10/10] Testing Lab Endpoints...")
    test_endpoint("/lab/dashboard/stats", "GET", token)
    
    # Print Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    total = len(test_results)
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    if failed > 0:
        print("\nFailed Tests:")
        for r in test_results:
            if r["status"] == "FAIL":
                print(f"  - {r['method']} {r['endpoint']}: {r['message']}")
    
    # Save results to file
    with open("/home/sujeetnew/Downloads/AXONHIS/backend/test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\nDetailed results saved to: test_results.json")
    print("=" * 80)

if __name__ == "__main__":
    run_all_tests()
