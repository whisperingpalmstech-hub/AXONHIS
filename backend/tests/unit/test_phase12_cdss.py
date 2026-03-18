"""
Phase 12 – CDSS (Clinical Decision Support System) Unit Tests
Tests the CDSS endpoints: check-medication, check-allergies, check-dose, alerts
"""
import pytest
from uuid import uuid4

test_patient_id = str(uuid4())
test_encounter_id = str(uuid4())


@pytest.mark.asyncio
async def test_cdss_medication_check_no_conflicts(client, auth_headers):
    """Test that a medication with no conflicts returns 'approved'"""
    payload = {
        "patient_context": {
            "patient_id": test_patient_id,
            "encounter_id": test_encounter_id,
            "weight_kg": 70,
            "age_years": 30,
            "kidney_function_egfr": 90,
            "allergies": [],
            "active_medications": [],
            "diagnoses": []
        },
        "new_medication_id": "drug_no_conflicts",
        "dose": 500
    }

    response = await client.post("/api/v1/cdss/check-medication", json=payload, headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "approved"
    assert len(data["alerts"]) == 0


@pytest.mark.asyncio
async def test_cdss_allergy_check_returns_valid_status(client, auth_headers):
    """Test that the allergy check endpoint returns a valid status field"""
    payload = {
        "patient_context": {
            "patient_id": test_patient_id,
            "encounter_id": test_encounter_id,
            "weight_kg": 70,
            "age_years": 30,
            "kidney_function_egfr": 90,
            "allergies": ["penicillin"],
            "active_medications": [],
            "diagnoses": []
        },
        "new_medication_id": "amoxicillin",
        "dose": 500
    }

    response = await client.post("/api/v1/cdss/check-allergies", json=payload, headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "status" in data
    assert data["status"] in ("approved", "warning", "blocked")


@pytest.mark.asyncio
async def test_cdss_dose_check_returns_valid_response(client, auth_headers):
    """Test that dose check endpoint returns a valid response"""
    payload = {
        "patient_context": {
            "patient_id": test_patient_id,
            "encounter_id": test_encounter_id,
            "weight_kg": 70,
            "age_years": 30,
            "kidney_function_egfr": 90,
            "allergies": [],
            "active_medications": [],
            "diagnoses": []
        },
        "new_medication_id": "drug_XYZ",
        "dose": 10000
    }

    response = await client.post("/api/v1/cdss/check-dose", json=payload, headers=auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "status" in data
    assert data["status"] in ("approved", "warning", "blocked")


@pytest.mark.asyncio
async def test_cdss_get_alerts_for_encounter(client, auth_headers):
    """Test that alerts endpoint returns a list (can be empty)"""
    response = await client.get(
        f"/api/v1/cdss/alerts/{test_encounter_id}",
        headers=auth_headers
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
