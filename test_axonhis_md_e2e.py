#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
 AXONHIS MD — END-TO-END TEST SUITE
 Tests the AxonHIS MD app (Unified Clinical Practice Platform)
═══════════════════════════════════════════════════════════════════════
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configuration
BASE_URL = "http://localhost:9503"
API_BASE_URL = "http://localhost:9500/api/v1"  # Backend API

# Test results
PASS = 0
FAIL = 0
SKIP = 0
RESULTS = []


def test(name: str, url: str, expected_status: int = 200, method: str = "GET", 
         headers: Optional[Dict] = None, data: Optional[Dict] = None) -> Tuple[bool, requests.Response]:
    """
    Execute a single test case
    Returns: (success, response)
    """
    global PASS, FAIL, SKIP
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        else:
            SKIP += 1
            print(f"  [{PASS+FAIL+SKIP:03d}] ⚠️  SKIP: {name} (Unsupported method)")
            return False, None
        
        success = response.status_code == expected_status
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  [{PASS+FAIL+SKIP:03d}] {status}: {name} ({response.status_code})")
        
        if success:
            PASS += 1
        else:
            FAIL += 1
            try:
                print(f"       → {response.text[:200]}")
            except:
                pass
        
        RESULTS.append({
            "name": name,
            "url": url,
            "method": method,
            "expected_status": expected_status,
            "actual_status": response.status_code,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
        return success, response
        
    except requests.exceptions.Timeout:
        FAIL += 1
        print(f"  [{PASS+FAIL+SKIP:03d}] ❌ FAIL: {name} (Timeout)")
        RESULTS.append({
            "name": name,
            "url": url,
            "method": method,
            "expected_status": expected_status,
            "actual_status": 0,
            "success": False,
            "error": "Timeout",
            "timestamp": datetime.now().isoformat()
        })
        return False, None
    except Exception as e:
        FAIL += 1
        print(f"  [{PASS+FAIL+SKIP:03d}] ❌ FAIL: {name} ({str(e)})")
        RESULTS.append({
            "name": name,
            "url": url,
            "method": method,
            "expected_status": expected_status,
            "actual_status": 0,
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
        return False, None


def section(title: str):
    """Print section header"""
    print(f"\n{'─' * 70}")
    print(f"  📋 {title}")
    print(f"{'─' * 70}")


def main():
    global PASS, FAIL, SKIP
    
    print("=" * 70)
    print("  AXONHIS MD — END-TO-END TEST SUITE")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  MD App URL: {BASE_URL}")
    print(f"  Backend API: {API_BASE_URL}")
    print("=" * 70)
    
    # ══════════════════════════════════════════════════════════════
    # MODULE 1: MD APP FRONTEND PAGES
    # ══════════════════════════════════════════════════════════════
    section("MODULE 1: MD App Frontend Pages")
    
    test("MD App Home Page", f"{BASE_URL}/", expected_status=200)
    test("MD App Login Page", f"{BASE_URL}/login", expected_status=200)
    test("MD App Dashboard", f"{BASE_URL}/dashboard", expected_status=200)
    
    # Test dashboard sub-pages
    test("MD App Dashboard - Patients", f"{BASE_URL}/dashboard/patients", expected_status=200)
    test("MD App Dashboard - Appointments", f"{BASE_URL}/dashboard/appointments", expected_status=200)
    test("MD App Dashboard - Encounters", f"{BASE_URL}/dashboard/encounters", expected_status=200)
    test("MD App Dashboard - Medications", f"{BASE_URL}/dashboard/medications", expected_status=200)
    
    # ══════════════════════════════════════════════════════════════
    # MODULE 2: BACKEND API - MD SPECIFIC ENDPOINTS
    # ══════════════════════════════════════════════════════════════
    section("MODULE 2: Backend API - MD Endpoints")
    
    # Authenticate with backend
    auth_success, auth_response = test("Backend Login", f"{API_BASE_URL}/auth/login", 
                            method="POST", 
                            data={"email": "admin@axonhis.com", "password": "Admin@123"})
    
    headers = {}
    if auth_success and auth_response and auth_response.status_code == 200:
        token = auth_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        print(f"       ✓ Authenticated with backend API")
    
    # Test MD-specific API endpoints
    test("MD Organizations", f"{API_BASE_URL}/axonhis-md/organizations", 
        headers=headers, expected_status=200)
    test("MD Facilities", f"{API_BASE_URL}/axonhis-md/facilities", 
        headers=headers, expected_status=200)
    test("MD Clinicians", f"{API_BASE_URL}/axonhis-md/clinicians", 
        headers=headers, expected_status=200)
    test("MD Patients", f"{API_BASE_URL}/axonhis-md/patients", 
        headers=headers, expected_status=200)
    test("MD Appointments", f"{API_BASE_URL}/axonhis-md/appointments", 
        headers=headers, expected_status=200)
    test("MD Encounters", f"{API_BASE_URL}/axonhis-md/encounters", 
        headers=headers, expected_status=200)
    test("MD Medications", f"{API_BASE_URL}/axonhis-md/medication-requests", 
        headers=headers, expected_status=200)
    test("MD Observations", f"{API_BASE_URL}/axonhis-md/observations", 
        headers=headers, expected_status=200)
    test("MD Documents", f"{API_BASE_URL}/axonhis-md/documents", 
        headers=headers, expected_status=200)
    
    # ══════════════════════════════════════════════════════════════
    # MODULE 3: MD APP WORKFLOW TESTS
    # ══════════════════════════════════════════════════════════════
    section("MODULE 3: MD App Workflow Tests")
    
    if headers:
        # Create a test patient via MD API
        patient_data = {
            "first_name": "MDTest",
            "last_name": f"Patient-{int(time.time())}",
            "gender": "male",
            "birth_date": "1990-05-15",
            "identifier_system": "http://hl7.org/fhir/sid/uhid",
            "identifier_value": f"MD-{int(time.time())}"
        }
        
        patient_response, _ = test("Create MD Patient", f"{API_BASE_URL}/axonhis-md/patients",
                                   method="POST", headers=headers, data=patient_data,
                                   expected_status=201)
        
        patient_id = None
        if patient_response and patient_response.status_code == 201:
            patient_id = patient_response.json().get("id")
            print(f"       ✓ Created MD patient: {patient_id}")
            
            # Create an appointment
            appointment_data = {
                "patient_id": patient_id,
                "clinician_id": "00000000-0000-0000-0000-000000000001",
                "status": "booked",
                "start": (datetime.now()).isoformat(),
                "end": (datetime.now()).isoformat()
            }
            
            appointment_response, _ = test("Create MD Appointment", 
                                          f"{API_BASE_URL}/axonhis-md/appointments",
                                          method="POST", headers=headers, data=appointment_data,
                                          expected_status=201)
            
            if appointment_response and appointment_response.status_code == 201:
                appointment_id = appointment_response.json().get("id")
                print(f"       ✓ Created MD appointment: {appointment_id}")
                
                # Create an encounter
                encounter_data = {
                    "patient_id": patient_id,
                    "clinician_id": "00000000-0000-0000-0000-000000000001",
                    "status": "in-progress",
                    "class": "ambulatory",
                    "type": [{"coding": [{"system": "http://hl7.org/fhir/encounter-type", "code": "consult"}]}]
                }
                
                encounter_response, _ = test("Create MD Encounter", 
                                            f"{API_BASE_URL}/axonhis-md/encounters",
                                            method="POST", headers=headers, data=encounter_data,
                                            expected_status=201)
                
                if encounter_response and encounter_response.status_code == 201:
                    encounter_id = encounter_response.json().get("id")
                    print(f"       ✓ Created MD encounter: {encounter_id}")
    
    # ══════════════════════════════════════════════════════════════
    # MODULE 4: INTEGRATION TESTS
    # ══════════════════════════════════════════════════════════════
    section("MODULE 4: Integration Tests")
    
    # Test that backend health check works
    test("Backend Health Check", f"{API_BASE_URL.replace('/api/v1', '')}/health", 
        expected_status=200)
    
    # Test that MD app can reach backend
    test("Backend API Reachability", f"{API_BASE_URL}/auth/me", 
        headers=headers, expected_status=401)  # Should fail without proper auth
    
    # ══════════════════════════════════════════════════════════════
    # FINAL REPORT
    # ══════════════════════════════════════════════════════════════
    total = PASS + FAIL
    duration = time.time() - time.time()  # Placeholder
    
    print("\n" + "═" * 70)
    print(f"  AXONHIS MD — END-TO-END TEST RESULTS")
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"═" * 70)
    print(f"  ✅ PASSED:  {PASS}/{total}")
    print(f"  ❌ FAILED:  {FAIL}/{total}")
    print(f"  ⚠️  SKIPPED: {SKIP}")
    print(f"{'═' * 70}")
    
    if total > 0:
        pass_rate = (PASS / total) * 100
        print(f"  📊 Pass Rate: {pass_rate:.1f}%")
    
    # Save results to JSON
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "passed": PASS,
            "failed": FAIL,
            "skipped": SKIP,
            "pass_rate": (PASS / total * 100) if total > 0 else 0
        },
        "results": RESULTS
    }
    
    report_file = f"axonhis_md_e2e_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"  📄 Report saved: {report_file}")
    print("═" * 70)
    
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
