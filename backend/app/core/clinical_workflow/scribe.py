"""
Module 2: Actionable Scribe — SOAP Notes + Auto-Order Generation.

Converts doctor findings into structured SOAP notes and auto-generates
order suggestions (labs, medications, imaging) with ICD-10 coding.
"""
import json
import logging
from typing import Any

from app.core.ai.grok_client import grok_json

logger = logging.getLogger(__name__)


SCRIBE_SYSTEM_PROMPT = """You are an Actionable Clinical Scribe AI — an expert medical documentation and order generation system.

Given a doctor's narrative findings, patient context, and encounter data, you MUST return a JSON object with this EXACT structure:

{
  "soap_note": {
    "subjective": {
      "chief_complaint": "",
      "hpi": "",
      "review_of_systems": {},
      "social_history": "",
      "family_history": ""
    },
    "objective": {
      "vitals": {},
      "physical_exam": {},
      "observations": []
    },
    "assessment": {
      "primary_diagnosis": {"description": "", "icd10": ""},
      "secondary_diagnoses": [{"description": "", "icd10": ""}],
      "clinical_reasoning": ""
    },
    "plan": {
      "summary": "",
      "follow_up": "",
      "patient_education": []
    }
  },
  "suggested_orders": {
    "medications": [
      {
        "drug": "",
        "dose": "",
        "route": "",
        "frequency": "",
        "duration": "",
        "indication": "",
        "priority": "stat|routine|prn"
      }
    ],
    "lab_tests": [
      {"test": "", "indication": "", "priority": "stat|routine", "specimen": ""}
    ],
    "imaging": [
      {"study": "", "indication": "", "priority": "stat|routine", "body_part": ""}
    ],
    "procedures": [
      {"procedure": "", "indication": "", "priority": "stat|routine"}
    ],
    "referrals": [
      {"specialty": "", "reason": "", "urgency": "immediate|soon|routine"}
    ]
  },
  "icd10_codes": [
    {"code": "", "description": "", "type": "primary|secondary"}
  ],
  "cpt_codes": [
    {"code": "", "description": ""}
  ],
  "clinical_alerts": [],
  "documentation_completeness": 0.0
}

RULES:
- Map ALL findings to appropriate ICD-10 codes
- Suggest orders based on clinical evidence
- Flag any incomplete documentation areas
- Prioritize stat orders appropriately
- Return valid JSON ONLY
"""


async def scribe(
    patient: dict[str, Any],
    encounter: dict[str, Any],
    navigator_output: dict[str, Any] | None = None,
    system_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run Actionable Scribe on doctor's findings.
    
    Args:
        patient: Patient demographics and history
        encounter: Doctor narrative, vitals, exam findings
        navigator_output: Optional output from Clinical Navigator
        system_context: Hospital protocols and formulary rules
    
    Returns:
        Structured SOAP note + order suggestions + coding.
    """
    user_message = _build_scribe_prompt(patient, encounter, navigator_output, system_context)
    
    messages = [
        {"role": "system", "content": SCRIBE_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    
    try:
        result = await grok_json(messages, temperature=0.2, max_tokens=2000)
        validation = _validate_scribe_output(result, patient, encounter)
        
        return {
            "module": "actionable_scribe",
            "module_output": result,
            "validation": validation,
            "test_cases": _generate_test_cases(),
            "improvements": [
                "Add formulary-aware medication suggestions",
                "Integrate previous encounter context for continuity",
                "Add voice-to-SOAP real-time transcription",
                "Support template-based documentation shortcuts"
            ],
            "next_step": "guardian"
        }
    except Exception as e:
        logger.error(f"Actionable Scribe error: {e}")
        return {
            "module": "actionable_scribe",
            "module_output": {},
            "validation": {
                "schema_valid": False,
                "missing_fields": [],
                "logic_issues": [f"AI processing failed: {str(e)}"],
                "safety_flags": ["Scribe unavailable — manual documentation required"]
            },
            "test_cases": [],
            "improvements": [],
            "next_step": "manual_documentation"
        }


def _build_scribe_prompt(
    patient: dict[str, Any],
    encounter: dict[str, Any],
    navigator_output: dict[str, Any] | None,
    system_context: dict[str, Any] | None,
) -> str:
    """Build the user prompt for the Scribe."""
    parts = []
    
    parts.append(f"PATIENT: Age {patient.get('age', 'unknown')}, Gender {patient.get('gender', 'unknown')}")
    
    history = patient.get("history", [])
    if history:
        parts.append(f"PMH: {', '.join(history)}")
    
    allergies = patient.get("allergies", [])
    if allergies:
        parts.append(f"ALLERGIES: {', '.join(allergies)}")
    
    medications = patient.get("medications", [])
    if medications:
        parts.append(f"CURRENT MEDS: {', '.join(medications)}")
    
    # Doctor's narrative
    doctor_input = encounter.get("doctor_input", "") or encounter.get("narrative", "")
    if doctor_input:
        parts.append(f"DOCTOR FINDINGS:\n{doctor_input}")
    
    # Vitals
    vitals = encounter.get("vitals", [])
    if vitals:
        vitals_str = ", ".join([f"{v.get('name', '')}: {v.get('value', '')}" for v in vitals])
        parts.append(f"VITALS: {vitals_str}")
    
    # Notes
    notes = encounter.get("notes", [])
    if notes:
        parts.append(f"ADDITIONAL NOTES: {'; '.join(notes)}")
    
    # Navigator context
    if navigator_output:
        nav = navigator_output.get("module_output", {})
        if nav:
            parts.append(f"TRIAGE ASSESSMENT: {nav.get('primary_impression', '')} (Severity: {nav.get('severity_score', 'N/A')})")
            diffs = nav.get("differential_diagnoses", [])
            if diffs:
                diff_str = ", ".join([d.get("diagnosis", "") for d in diffs[:3]])
                parts.append(f"DIFFERENTIALS: {diff_str}")
    
    return "\n".join(parts)


def _validate_scribe_output(result: dict, patient: dict, encounter: dict) -> dict:
    """Validate Scribe output."""
    missing = []
    issues = []
    safety_flags = []
    
    # Schema checks
    if "soap_note" not in result:
        missing.append("soap_note")
    else:
        soap = result["soap_note"]
        for section in ["subjective", "objective", "assessment", "plan"]:
            if section not in soap:
                missing.append(f"soap_note.{section}")
    
    if "suggested_orders" not in result:
        missing.append("suggested_orders")
    
    if "icd10_codes" not in result:
        missing.append("icd10_codes")
    
    # Clinical logic
    orders = result.get("suggested_orders", {})
    meds = orders.get("medications", [])
    allergies = set(a.lower() for a in patient.get("allergies", []))
    
    for med in meds:
        drug = med.get("drug", "").lower()
        for allergy in allergies:
            if allergy in drug or drug in allergy:
                safety_flags.append(f"CRITICAL: Suggested medication '{med.get('drug')}' may conflict with allergy '{allergy}'")
    
    # Completeness
    completeness = result.get("documentation_completeness", 0)
    if completeness < 0.7:
        issues.append(f"Documentation completeness {completeness:.0%} — below threshold")
    
    return {
        "schema_valid": len(missing) == 0,
        "missing_fields": missing,
        "logic_issues": issues,
        "safety_flags": safety_flags,
    }


def _generate_test_cases() -> list[dict]:
    return [
        {
            "name": "Complete consultation note",
            "input": {"doctor_input": "Patient presents with productive cough x5 days, fever 101F, crackles left base"},
            "expected_behavior": "Full SOAP note, CBC/CXR orders, antibiotic suggestion, pneumonia ICD-10"
        },
        {
            "name": "Edge case — minimal input",
            "input": {"doctor_input": "Headache"},
            "expected_behavior": "Partial SOAP with low completeness score, request more info"
        },
        {
            "name": "Failure case — allergy conflict",
            "input": {"doctor_input": "UTI, prescribe amoxicillin", "allergies": ["penicillin"]},
            "expected_behavior": "Safety flag for penicillin cross-reactivity"
        },
    ]
