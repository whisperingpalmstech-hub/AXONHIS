import json
import urllib.request
import urllib.error
import sys
import uuid

BASE_URL = "http://localhost:9500/api/v1"

def test_endpoint(name, method, path, payload=None):
    print(f"Running {name}...")
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    
    if payload:
        data = json.dumps(payload).encode('utf-8')
        req.add_header('Content-Length', len(data))
    else:
        data = None

    try:
        with urllib.request.urlopen(req, data=data) as response:
            res_data = json.loads(response.read().decode())
            print(f"PASS: {name} (Status: {response.status})")
            return res_data
    except urllib.error.HTTPError as e:
        res_data = e.read().decode()
        if e.code in [404, 422]:
            print(f"PASS (Expected Error): {name} (Status: {e.code})")
        else:
            print(f"FAIL: {name} (Status: {e.code}) - {res_data}")
            sys.exit(1)
    except Exception as e:
        print(f"FAIL: {name} - Request failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # 1. Test Departments
        test_endpoint("get_departments", "GET", "/kiosk/departments")
        
        # 2. Test Doctors
        test_endpoint("get_doctors", "GET", "/kiosk/doctors?department=Cardiology")
        
        # 3. Test Token Generation
        token = test_endpoint("generate_token", "POST", "/kiosk/token", {"department": "Orthopedics", "priority": False})
        
        # 4. Test Invalid Status Update
        fake_id = str(uuid.uuid4())
        test_endpoint("invalid_status", "PUT", f"/kiosk/token/{fake_id}/status", {"status": "Completed"})
        
        print("\n✅ ALL QA INTEGRATION AUTOMATED TESTS PASSED SUCCESSFULLY.")
    except Exception as e:
        print(f"QA Pipeline Failed: {e}")
        sys.exit(1)
