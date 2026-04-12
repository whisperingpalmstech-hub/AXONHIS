import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

def generate_fhir_patient(patient_id: str, first_name: str, last_name: str, gender: str, dob: str) -> Dict[str, Any]:
    """Generates a FHIR Patient Resource."""
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "identifier": [
            {
                "system": "https://healthid.ndhm.gov.in",
                "value": patient_id
            }
        ],
        "name": [
            {
                "use": "official",
                "family": last_name,
                "given": [first_name]
            }
        ],
        "gender": gender.lower() if gender else "unknown",
        "birthDate": dob
    }

def generate_fhir_bundle(resources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Wraps resources in a FHIR Bundle."""
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entry": [{"resource": res} for res in resources]
    }

def generate_fhir_prescription(enc_id: str, patient_id: str, doctor_id: str, meds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generates a FHIR MedicationRequest Resource."""
    entries = []
    for med in meds:
        entries.append({
            "resourceType": "MedicationRequest",
            "id": str(uuid.uuid4()),
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "text": med.get("name", "Unknown Medication")
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "encounter": {"reference": f"Encounter/{enc_id}"},
            "authoredOn": datetime.now(timezone.utc).isoformat(),
            "requester": {"reference": f"Practitioner/{doctor_id}"},
            "dosageInstruction": [
                {
                    "text": med.get("dosage", "")
                }
            ]
        })
    return entries
