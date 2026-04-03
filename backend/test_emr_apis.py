import requests
import json
import uuid

API_BASE = "http://localhost:9500/api/v1/doctor-desk"

def test_api():
    # Login to get token
    login_resp = requests.post("http://localhost:9500/api/v1/auth/login", json={
        "email": "admin@axonhis.com", "password": "Admin@123"
    })
    token = login_resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    visit_id = str(uuid.uuid4())
    patient_id = str(uuid.uuid4())
    
    # 1. Test complaints
    resp = requests.post(f"{API_BASE}/advanced/complaints", headers=headers, json={
        "visit_id": visit_id,
        "patient_id": patient_id,
        "encounter_type": "opd",
        "icpc_code": "A01",
        "complaint_description": "Fever, 3 days",
        "severity": "Moderate"
    })
    print("Complaints POST:", resp.status_code)
    
    # 2. Test Vitals
    resp = requests.post(f"{API_BASE}/advanced/vitals", headers=headers, json={
        "visit_id": visit_id,
        "patient_id": patient_id,
        "temperature": "38",
        "bp_systolic": 120,
        "bp_diastolic": 80,
        "height_cm": "170",
        "weight_kg": "70"
    })
    print("Vitals POST:", resp.status_code, resp.json().get("bmi"))
    
    # 3. Test Medical History
    resp = requests.post(f"{API_BASE}/advanced/medical-history", headers=headers, json={
        "patient_id": patient_id,
        "category": "allergy",
        "description": "Peanuts"
    })
    print("History POST:", resp.status_code)

if __name__ == "__main__":
    test_api()
