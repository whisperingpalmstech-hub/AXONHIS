import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_kiosk_get_departments():
    response = client.get("/api/v1/kiosk/departments")
    assert response.status_code == 200, "Should successfully fetch departments"
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "name" in data[0]

def test_kiosk_get_doctors():
    response = client.get("/api/v1/kiosk/doctors?department_name=Cardiology")
    assert response.status_code == 200, "Should successfully fetch doctors for department"
    data = response.json()
    assert isinstance(data, list)

def test_kiosk_generate_token():
    payload = {
        "department": "Orthopedics",
        "priority": False
    }
    response = client.post("/api/v1/kiosk/queue/token", json=payload)
    if response.status_code == 200:
        data = response.json()
        assert "token_display" in data
        assert data["department"] == "Orthopedics"
        assert data["status"] == "Pending"
    else:
        # If API is not fully configured to mock, it may 500, we catch it
        pytest.fail(f"Token generation failed: {response.text}")

def test_kiosk_invalid_status_update():
    # Updating a fake token should return 404 cleanly, not 500
    fake_id = str(uuid.uuid4())
    payload = {"status": "Completed"}
    response = client.put(f"/api/v1/kiosk/queue/{fake_id}/status", json=payload)
    assert response.status_code in [404, 422], f"Expected 404 or 422, got {response.status_code} - {response.text}"
