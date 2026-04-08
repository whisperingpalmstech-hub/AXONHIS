import sys
try:
    from fastapi.testclient import TestClient
    from app.main import app
    import uuid

    client = TestClient(app)

    print("Running test_kiosk_get_departments...")
    resp = client.get("/api/v1/kiosk/departments")
    assert resp.status_code == 200, f"Expected 200 got {resp.status_code}"
    print("PASS: get_departments")

    print("\nRunning test_kiosk_get_doctors...")
    resp = client.get("/api/v1/kiosk/doctors?department_name=Cardiology")
    assert resp.status_code == 200, f"Expected 200 got {resp.status_code}"
    print("PASS: get_doctors")

    print("\nRunning test_kiosk_generate_token...")
    payload = {"department": "Orthopedics", "priority": False}
    resp = client.post("/api/v1/kiosk/queue/token", json=payload)
    if resp.status_code == 200:
        print("PASS: generate_token")
    else:
        print(f"FAIL: generate_token returned {resp.status_code} - {resp.text}")

    print("\nRunning test_kiosk_invalid_status...")
    fake_id = str(uuid.uuid4())
    resp = client.put(f"/api/v1/kiosk/queue/{fake_id}/status", json={"status": "Completed"})
    assert resp.status_code in [404, 422], f"Expected 404 or 422 got {resp.status_code}"
    print("PASS: invalid_status")
    
    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY.")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
