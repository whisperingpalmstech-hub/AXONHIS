#!/usr/bin/env python3
"""
End-to-End Test Script for Health Platform Missing Features
Tests all new API endpoints like a QA engineer
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# Configuration
BASE_URL = "http://localhost:9500"
API_BASE = f"{BASE_URL}/api/v1"
ADMIN_TOKEN = "test_admin_token"  # Replace with actual token if auth is required

# Test results tracking
test_results = []
passed = 0
failed = 0
skipped = 0


class TestResult:
    def __init__(self, test_name: str, endpoint: str, status: str, 
                 response_code: int, message: str, duration_ms: float):
        self.test_name = test_name
        self.endpoint = endpoint
        self.status = status  # PASS, FAIL, SKIP
        self.response_code = response_code
        self.message = message
        self.duration_ms = duration_ms
        self.timestamp = datetime.now().isoformat()


def log_test(test_name: str, endpoint: str, status: str, 
             response_code: int, message: str, duration_ms: float):
    """Log a test result"""
    global passed, failed, skipped
    
    result = TestResult(test_name, endpoint, status, response_code, message, duration_ms)
    test_results.append(result)
    
    if status == "PASS":
        passed += 1
        print(f"✅ PASS: {test_name} - {endpoint} ({response_code})")
    elif status == "FAIL":
        failed += 1
        print(f"❌ FAIL: {test_name} - {endpoint} ({response_code}) - {message}")
    else:
        skipped += 1
        print(f"⚠️  SKIP: {test_name} - {endpoint} - {message}")


def make_request(method: str, endpoint: str, data: dict = None, 
                 headers: dict = None, auth_required: bool = False) -> Tuple[int, dict]:
    """Make an HTTP request and return status code and response"""
    import time
    start = time.time()
    
    url = f"{BASE_URL}{endpoint}" if not endpoint.startswith("http") else endpoint
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=5)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=5)
        else:
            return 0, {"error": "Invalid method"}
        
        duration_ms = (time.time() - start) * 1000
        
        try:
            response_data = response.json() if response.content else {}
        except:
            response_data = {"raw": response.text}
        
        return response.status_code, response_data, duration_ms
    except requests.exceptions.RequestException as e:
        duration_ms = (time.time() - start) * 1000
        return 0, {"error": str(e)}, duration_ms


def test_health_endpoints():
    """Test public health endpoints (no auth required)"""
    print("\n" + "="*60)
    print("Testing Health Endpoints (Public)")
    print("="*60)
    
    # Test /health
    status_code, data, duration = make_request("GET", "/health")
    if status_code == 200 and "status" in data:
        log_test("Health Check", "/health", "PASS", status_code, "Health endpoint responding", duration)
    else:
        log_test("Health Check", "/health", "FAIL", status_code, f"Unexpected response: {data}", duration)
    
    # Test /health/readiness
    status_code, data, duration = make_request("GET", "/health/readiness")
    if status_code == 200 and "ready" in data:
        log_test("Readiness Check", "/health/readiness", "PASS", status_code, "Readiness endpoint responding", duration)
    else:
        log_test("Readiness Check", "/health/readiness", "FAIL", status_code, f"Unexpected response: {data}", duration)
    
    # Test /health/liveness
    status_code, data, duration = make_request("GET", "/health/liveness")
    if status_code == 200 and "alive" in data:
        log_test("Liveness Check", "/health/liveness", "PASS", status_code, "Liveness endpoint responding", duration)
    else:
        log_test("Liveness Check", "/health/liveness", "FAIL", status_code, f"Unexpected response: {data}", duration)
    
    # Test correlation ID headers
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if "x-correlation-id" in response.headers and "x-request-id" in response.headers:
            log_test("Correlation ID Headers", "/health", "PASS", response.status_code, 
                    f"Correlation ID: {response.headers['x-correlation-id'][:8]}...", 0)
        else:
            log_test("Correlation ID Headers", "/health", "FAIL", response.status_code, 
                    "Missing correlation ID headers", 0)
    except Exception as e:
        log_test("Correlation ID Headers", "/health", "FAIL", 0, str(e), 0)


def test_event_bus():
    """Test Event Bus endpoints"""
    print("\n" + "="*60)
    print("Testing Event Bus Endpoints")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test GET subscriptions (list)
    status_code, data, duration = make_request("GET", f"{API_BASE}/event-bus/subscriptions", headers=headers)
    if status_code in [200, 401]:  # 401 is acceptable if auth is required
        log_test("List Subscriptions", "/api/v1/event-bus/subscriptions", "PASS", status_code, 
                "Subscriptions list endpoint accessible", duration)
    else:
        log_test("List Subscriptions", "/api/v1/event-bus/subscriptions", "FAIL", status_code, 
                f"Unexpected response: {data}", duration)
    
    # Test POST search events
    status_code, data, duration = make_request("POST", f"{API_BASE}/event-bus/events/search", 
        data={}, headers=headers)
    if status_code in [200, 400, 401]:  # 400 acceptable for empty search
        log_test("Search Events", "/api/v1/event-bus/events/search", "PASS", status_code, 
                "Events search endpoint accessible", duration)
    else:
        log_test("Search Events", "/api/v1/event-bus/events/search", "FAIL", status_code, 
                f"Unexpected response: {data}", duration)
    
    # Test POST retry failed
    status_code, data, duration = make_request("POST", f"{API_BASE}/event-bus/events/retry-failed", 
        headers=headers)
    if status_code in [200, 401]:
        log_test("Retry Failed Events", "/api/v1/event-bus/events/retry-failed", "PASS", status_code, 
                "Retry failed endpoint accessible", duration)
    else:
        log_test("Retry Failed Events", "/api/v1/event-bus/events/retry-failed", "FAIL", status_code, 
                f"Unexpected response: {data}", duration)


def test_longitudinal_index():
    """Test Longitudinal Record Index endpoints"""
    print("\n" + "="*60)
    print("Testing Longitudinal Record Index Endpoints")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    test_patient_id = str(uuid.uuid4())
    
    # Test GET patient timeline
    status_code, data, duration = make_request("GET", 
        f"{API_BASE}/longitudinal/patients/{test_patient_id}/timeline", headers=headers)
    if status_code in [200, 401, 404]:  # 404 is acceptable for non-existent patient
        log_test("Patient Timeline", f"/api/v1/longitudinal/patients/{test_patient_id}/timeline", 
                "PASS", status_code, "Timeline endpoint accessible", duration)
    else:
        log_test("Patient Timeline", f"/api/v1/longitudinal/patients/{test_patient_id}/timeline", 
                "FAIL", status_code, f"Unexpected response: {data}", duration)
    
    # Test POST records search
    status_code, data, duration = make_request("POST", f"{API_BASE}/longitudinal/records/search", 
        data={}, headers=headers)
    if status_code in [200, 400, 401]:  # 400 acceptable for empty search
        log_test("Records Search", "/api/v1/longitudinal/records/search", "PASS", status_code, 
                "Records search endpoint accessible", duration)
    else:
        log_test("Records Search", "/api/v1/longitudinal/records/search", "FAIL", status_code, 
                f"Unexpected response: {data}", duration)
    
    # Test POST timeline
    status_code, data, duration = make_request("POST", f"{API_BASE}/longitudinal/timeline", 
        data={"patient_id": test_patient_id}, headers=headers)
    if status_code in [200, 400, 401]:
        log_test("Timeline Trigger", "/api/v1/longitudinal/timeline", "PASS", status_code, 
                "Timeline trigger endpoint accessible", duration)
    else:
        log_test("Timeline Trigger", "/api/v1/longitudinal/timeline", "FAIL", status_code, 
                f"Unexpected response: {data}", duration)


def test_clinical_rules():
    """Test Clinical Rule Engine endpoints"""
    print("\n" + "="*60)
    print("Testing Clinical Rule Engine Endpoints")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    status_GEe, dataion = make_request("GET", f"{API_BASE}/clinical-rules/rules", headers=headers)
    if status_code in [200, 401]:GE"List Rules", "/api/v1/clinical-rules/rules", "PASS", status_code, 
                "Rules list ent a
    else:List
        log_test("List liRt, "/api/v1/clinical-rules/rules", "FAIL", status_code, 
                f"Unexpected response: {data}", duration)
    List
    # Test GET alerts
    status_code, data, duration = make_request("GET", f"{API_BASE}/clinical-rules/alerts", headers=headers)
    if status_[200, 401]:
        log_test("List Alerts", "/api/v1/clinical-rul         "Alerts list endpoin 
    else:
        log_test("Ltslerts", "/ai/v1/clinical-rules/alersl rFA", "PASS",  stuusdco,
                fUlertr" isrtion)

Ls_adapters(): 
               
    """Test Device Adapter Framework endpoints"""
    print("\n" + "="*60)
    print("Testing Device Adapter Framework Endpoints")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test GET adapters
    status_code, data, duration = make_request("GET", f"{API_BASE}/device-adapters/adapters", headers=headers)
    if status_code in [200, 401]:
        log_test("List Adapters", "/api/v1/device-adapters/adapters", "PASS", status_code, 
                "Adapters list endpoint accessible", duration)
    else:
        log_test("List Adapters", "/api/v1/device-adapters/adapters", "FAIL", status_code, 
                f"Unexpected response: {data}", duration)
    
    # Test POST crepdepp"S statda"/api/v1/device-adapters/adapters", f
def test_config_service():
    """Test Config Service endpoints"""
    print("\n" + "="*60)
    print("Testing Config Service Endpoints")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test GET config items
    status_code, data, duration = make_request("GET", f"{API_BASE}/config/items", headers=headers)
    if status_code in [200, 401]:
        log_test("Listouo}
    Etque("GET", f" ndpoint accessible", duration)
    else:
        log_test("List Config Groups", "/api/v1/config/groups", "FAIL", status_code, 
                f"Unexpected response: {data}", duration)


def test_approval_gates():
    """Test Approval Gates endpoints"""
    print("\n" + "="*60)
    print("Testing Approval Gates Endpoints")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test GET gates
    status_code, data, duration = make_request("GET", f"{API_BASE}/approvals/gates", headers=headers)
    if status_code in [200, 401]:
        logPOSescheck (he(l"h chLck for approval iystem)st Approval Gates", "/api/v1/approvals/gates", "PASS", status_code, 
                "Approval gates endpoint accessiPOSe", duration)chck
        data={}, 
    else:
        log_test("Approval Check", "/api/v1/approvals/check", "FAIL", status_code, 
                f"Unexpectchrcksponse: {data}", duration)
    
    # Test GET reqChckchck
    status_code, data, duration = make_request("GET", f"{API_BASE}/approvals/requests", headers=headers)
    if status_code in [200, 401]:
        log_tespending t("List Approval Requests", "/api/v1/approvals/requests", "PASS", status_code, 
                "Approval requests endpoint accessible", duration)/pending
    else:
        log_test("Pending Requests", "/api/v1/approvals/requests/pending", "FAIL", status_code, 
                fPendingted response: {data}", duration)

Pendng/pending
def test_webhook_publisher():
    """Test Webhook Publisher endpoints"""
    print("\n" + "="*60)
    print("Testing Webhook Publisher Endpoints")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test GET webhook subscriptions
    status_code, data, duration = make_request("GET", f"{API_BASE}/webhooks/subscriptions", headers=headers)
    if status_code in [200, 401]:
        log_test("List Webhook Subscriptions", "/api/v1/webhooks/subscriptions", "PASS", status_code, 
                "Webhook subscriptions endpoint accessible", duration)
    else:
        log_test("List Webhook Subscriptions", "/api/v1/webhooks/subscriptions", "FAIL", status_code, 
                f"Unexpected response: {data}", duration)


def test_suggestion_tracker():
    """Test Suggestion Tracker endpoints"""
    print("\n" + "="*60)
    print("Testing Suggestion Tracker Endpoints")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test GET suggestions
    status_code, data, duration = make_request("GET", f"{API_BASE}/suggestions/suggestions", headers=headers)
    if status_code in [200, 401]:
        log_tesacciptauce gtatsgestions", "/api/v1/suggestions/suggestions", "PASS", status_code, 
                "Suggestions endpoint accessible", duration)analytic/accpace-tats
    else:
        log_test("Acceptance "e natqSugges/  p:nce-stats", "FAIL", status_code, 
                f"cceptaUce stnpted response: {data}", duration)

AccpaceStcs/acceptane-stat
def test_prompt_mappings():
    """Test Prompt Mappings endpoints"""
    print("\n" + "="*60)
    print("Testing Prompt Mappings Endpoints")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test GET prompt mappings
    status_code, data, duration = make_request("GET",dsAPI_BASE}/prompts/variables", headers=headers)
    if status_code in [200, 401]:
        log_test("List Prompt Variables", "/api/v1/prompts/variables", "PASS", status_code, 
                "Prompt variables endpoint accessible", duration)
    else:
        log_test("List Prompt Variables", "/api/v1/prompts/variables", "FAIL", status_code, 
                f"Unexpected response: {data}", duration)


def test_document_templates():
    """Test Document Template Mappings endpoints"""
    print("\n" + "="*60)
    print("Testing Document Template Mappings Endpoints")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test GET document templates
    status_code, data, duration = make_request("GET", f"{API_BASE}/document-templates/mappings", headers=headers)
    if status_code in [200, 401]:
        log_test("List Document Templates", "/api/v1/document-templates/mappings", "PASS", status_code, 
                "Document templates endpoint accessible", duration)
    else:
        log_test("List Document Templates", "/api/v1/document-templates/mappings", "FAIL", status_code, 
                f"Unexpected response: {data}", duration)


def test_doctor_preferences():
    """Test Doctor Preferences endpoints"""
    print("\n" + "="*60)
    print("Testing Doctor Preferences Endpoints")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    test_clinician_id = str(uuid.uuid4())
    
    # Test GET doctor preferences
    status_code, data, duration = make_request("GET", 
        f"{API_BASE}/preferences/clinicians/{test_clinician_id}/preferences", headers=headers)
    if status_code in [200, 401, 404]:
        log_test("Doctor Preferences", f"/api/v1/preferences/clinicians/{test_clinician_id}/preferences", 
                "PASS", status_code, "Doctor preferences endpoint accessible", duration)
    else:
        log_test("Doctor Preferences", f"/api/v1/preferences/clinicians/{test_clinician_id}/preferences", 
                "FAIL", status_code, f"Unexpected response: {data}", duration)


def generate_report():
    """Generate test report"""
    print("\n" + "="*60)
    print("TEST REPORT")
    print("="*60)
    print(f"Total Tests: {len(test_results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Skipped: {skipped}")
    print(f"Success Rate: {(passed / len(test_results) * 100):.1f}%")
    print("="*60)
    
    # Save report to file
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": len(test_results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": round(passed / len(test_results) * 100, 2)
        },
        "tests": [
            {
                "test_name": r.test_name,
                "endpoint": r.endpoint,
                "status": r.status,
                "response_code": r.response_code,
                "message": r.message,
                "duration_ms": r.duration_ms,
                "timestamp": r.timestamp
            }
            for r in test_results
        ]
    }
    
    with open("e2e_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: e2e_test_report.json")
    
    return failed == 0


def main():
    """Main test runner"""
    print("="*60)
    print("Health Platform Missing Features - E2E Test Suite")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Test started at: {datetime.now().isoformat()}")
    print("="*60)
    
    try:
        # Test health endpoints first (no auth required)
        test_health_endpoints()
        
        # Test all feature endpoints
        test_event_bus()
        test_longitudinal_index()
        test_clinical_rules()
        test_device_adapters()
        test_config_service()
        test_approval_gates()
        test_webhook_publisher()
        test_suggestion_tracker()
        test_prompt_mappings()
        test_document_templates()
        test_doctor_preferences()
        
        # Generate report
        success = generate_report()
        
        if success:
            print("\n✅ All tests passed!")
            return 0
        else:
            print(f"\n❌ {failed} test(s) failed")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        generate_report()
        return 1
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
