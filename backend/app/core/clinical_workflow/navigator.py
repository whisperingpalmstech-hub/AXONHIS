"""
Module 1: Clinical Navigator — Intake Intelligence Engine.

Analyzes patient symptoms/complaints → produces structured triage output
with severity, differential diagnoses, and routing recommendations.
"""
import json
import logging
from typing import Any

from app.core.ai.grok_client import grok_json

logger = logging.getLogger(__name__)


NAVIGATOR_SYSTEM_PROMPT = """You are a Clinical Navigator AI — an expert triage and intake intelligence system.

Given a patient's presenting complaint, vitals, demographics, and medical history, you MUST return a JSON object with this EXACT structure:

{
  "triage_level": "ESI-1|ESI-2|ESI-3|ESI-4|ESI-5",
  "triage_color": "red|orange|yellow|green|blue",
  "severity_score": 1-10,
  "primary_impression": "Most likely diagnosis",
  "differential_diagnoses": [
    {"diagnosis": "", "icd10": "", "probability": 0.0, "reasoning": ""}
  ],
  "red_flags": ["List of critical findings requiring immediate attention"],
  "recommended_routing": {
    "department": "",
    "urgency": "immediate|urgent|semi_urgent|routine",
    "specialist": ""
  },
  "recommended_workup": {
    "labs": [""],
    "imaging": [""],
    "procedures": [""]
  },
  "risk_assessment": {
    "sepsis_risk": "low|moderate|high",
    "cardiac_risk": "low|moderate|high",
    "falls_risk": "low|moderate|high",
    "overall_acuity": "critical|high|moderate|low"
  },
  "clinical_summary": "Brief 2-3 sentence clinical summary"
}

RULES:
- NEVER assume missing data — flag it as missing
- ALWAYS check for red flags first
- Consider patient age, gender, and history in your assessment
- Return valid JSON ONLY
"""


async def navigate(
    patient: dict[str, Any],
    encounter: dict[str, Any],
    system_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run Clinical Navigator on patient intake data.
    
    Args:
        patient: {id, age, gender, history[], allergies[], medications[]}
        encounter: {narrative, vitals[], notes[]}
        system_context: {protocols[], hospital_rules[]}
    
    Returns:
        Structured triage and routing output.
    """
    # Build clinical context message
    user_message = _build_navigator_prompt(patient, encounter, system_context)
    
    messages = [
        {"role": "system", "content": NAVIGATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    
    try:
        result = await grok_json(messages, temperature=0.2, max_tokens=1500)
        
        # Validate output
        validation = _validate_navigator_output(result, patient)
        
        return {
            "module": "clinical_navigator",
            "module_output": result,
            "validation": validation,
            "test_cases": _generate_test_cases(patient, encounter),
            "improvements": [
                "Add protocol-specific triage rules for local hospital",
                "Integrate real-time lab results for dynamic re-triage",
                "Add NEWS2/MEWS scoring integration"
            ],
            "next_step": "actionable_scribe"
        }
    except Exception as e:
        logger.error(f"Clinical Navigator error: {e}")
        return {
            "module": "clinical_navigator",
            "module_output": {},
            "validation": {
                "schema_valid": False,
                "missing_fields": [],
                "logic_issues": [f"AI processing failed: {str(e)}"],
                "safety_flags": ["Navigator unavailable — manual triage required"]
            },
            "test_cases": [],
            "improvements": [],
            "next_step": "manual_triage"
        }


def _build_navigator_prompt(
    patient: dict[str, Any],
    encounter: dict[str, Any],
    system_context: dict[str, Any] | None,
) -> str:
    """Build the user prompt for the Navigator."""
    parts = []
    
    # Patient demographics
    parts.append(f"PATIENT: Age {patient.get('age', 'unknown')}, Gender {patient.get('gender', 'unknown')}")
    
    # History
    history = patient.get("history", [])
    if history:
        parts.append(f"MEDICAL HISTORY: {', '.join(history)}")
    else:
        parts.append("MEDICAL HISTORY: None reported (FLAG: incomplete history)")
    
    # Allergies
    allergies = patient.get("allergies", [])
    if allergies:
        parts.append(f"ALLERGIES: {', '.join(allergies)}")
    else:
        parts.append("ALLERGIES: NKDA (No Known Drug Allergies)")
    
    # Current medications
    medications = patient.get("medications", [])
    if medications:
        parts.append(f"CURRENT MEDICATIONS: {', '.join(medications)}")
    
    # Presenting complaint
    narrative = encounter.get("narrative", "")
    if narrative:
        parts.append(f"PRESENTING COMPLAINT: {narrative}")
    
    # Doctor input
    doctor_input = encounter.get("doctor_input", "")
    if doctor_input:
        parts.append(f"DOCTOR NOTES: {doctor_input}")
    
    # Vitals
    vitals = encounter.get("vitals", [])
    if vitals:
        vitals_str = ", ".join([f"{v.get('name', '')}: {v.get('value', '')}" for v in vitals])
        parts.append(f"VITALS: {vitals_str}")
    
    # System context
    if system_context:
        protocols = system_context.get("protocols", [])
        if protocols:
            parts.append(f"HOSPITAL PROTOCOLS: {', '.join(protocols)}")
    
    return "\n".join(parts)


def _validate_navigator_output(result: dict, patient: dict) -> dict:
    """Validate the Navigator output for safety and completeness."""
    missing = []
    issues = []
    safety_flags = []
    
    # Schema checks
    required_fields = ["triage_level", "severity_score", "primary_impression", 
                       "differential_diagnoses", "recommended_routing"]
    for field in required_fields:
        if field not in result:
            missing.append(field)
    
    # Clinical logic checks
    severity = result.get("severity_score", 0)
    triage = result.get("triage_level", "")
    
    if severity >= 8 and triage not in ["ESI-1", "ESI-2"]:
        issues.append(f"Severity {severity} but triage {triage} — mismatch")
    
    if severity <= 3 and triage in ["ESI-1", "ESI-2"]:
        issues.append(f"Low severity {severity} with high triage {triage} — verify")
    
    # Safety checks
    red_flags = result.get("red_flags", [])
    if red_flags and triage not in ["ESI-1", "ESI-2", "ESI-3"]:
        safety_flags.append("Red flags present but triage level may be too low")
    
    if not patient.get("history"):
        safety_flags.append("Incomplete medical history — triage may be inaccurate")
    
    if not patient.get("allergies"):
        safety_flags.append("Allergy status unconfirmed — verify before ordering")
    
    return {
        "schema_valid": len(missing) == 0,
        "missing_fields": missing,
        "logic_issues": issues,
        "safety_flags": safety_flags,
    }


def _generate_test_cases(patient: dict, encounter: dict) -> list[dict]:
    """Generate test cases for this Navigator run."""
    return [
        {
            "name": "Normal triage case",
            "input": {"narrative": "Mild headache for 2 days", "age": 35},
            "expected_behavior": "ESI-4 or ESI-5, low severity, outpatient routing"
        },
        {
            "name": "Edge case — chest pain with cardiac history",
            "input": {"narrative": "Crushing chest pain", "history": ["MI 2022"]},
            "expected_behavior": "ESI-1 or ESI-2, cardiac red flags, immediate ER"
        },
        {
            "name": "Failure case — empty narrative",
            "input": {"narrative": "", "age": 50},
            "expected_behavior": "Return partial output with missing_fields warning"
        },
    ]
