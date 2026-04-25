"""
Module 5: Patient Translator — Human-Friendly Clinical Output.

Converts clinical documentation into patient-friendly language
for discharge instructions, care plans, and health literacy.
"""
import json
import logging
from typing import Any

from app.core.ai.grok_client import grok_json

logger = logging.getLogger(__name__)


TRANSLATOR_SYSTEM_PROMPT = """You are a Patient Translator AI — an expert at converting complex medical documentation into simple, patient-friendly language.

Given clinical notes, discharge summaries, or care plans, translate them into language a non-medical person can understand.

Return a JSON object with this EXACT structure:

{
  "patient_summary": {
    "title": "",
    "what_happened": "",
    "what_we_found": "",
    "what_it_means": "",
    "what_to_do_next": ""
  },
  "medications_explained": [
    {
      "medicine_name": "",
      "what_its_for": "",
      "how_to_take": "",
      "common_side_effects": [],
      "when_to_call_doctor": [],
      "important_warnings": []
    }
  ],
  "care_instructions": [
    {
      "category": "diet|activity|wound_care|follow_up|medication|warning_signs",
      "instruction": "",
      "priority": "must_do|should_do|optional",
      "icon": "pill|food|activity|bandage|calendar|alert"
    }
  ],
  "warning_signs": [
    {
      "symptom": "",
      "action": "call_doctor|go_to_er|monitor",
      "urgency": "immediate|within_24h|next_visit"
    }
  ],
  "follow_up_appointments": [
    {
      "when": "",
      "with_whom": "",
      "purpose": "",
      "preparation": ""
    }
  ],
  "faq": [
    {
      "question": "",
      "answer": ""
    }
  ],
  "reading_level": "grade_5|grade_8|grade_12",
  "language": "en"
}

RULES:
- Use 5th-grade reading level by default
- NO medical jargon — explain everything simply
- Include visual cues (icons) for each instruction
- Always include warning signs section
- Be warm, reassuring, but honest
- Return valid JSON ONLY
"""


async def translate(
    clinical_content: dict[str, Any],
    patient: dict[str, Any] | None = None,
    target_language: str = "en",
    reading_level: str = "grade_5",
) -> dict[str, Any]:
    """
    Translate clinical content into patient-friendly language.
    
    Args:
        clinical_content: Clinical notes, discharge summary, SOAP note, or orders
        patient: Patient demographics for personalization
        target_language: Target language code
        reading_level: Target reading level
    
    Returns:
        Patient-friendly translation.
    """
    user_message = _build_translator_prompt(clinical_content, patient, target_language, reading_level)
    
    messages = [
        {"role": "system", "content": TRANSLATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    
    try:
        result = await grok_json(messages, temperature=0.3, max_tokens=2000)
        validation = _validate_translator_output(result)
        
        return {
            "module": "patient_translator",
            "module_output": result,
            "validation": validation,
            "test_cases": _generate_test_cases(),
            "improvements": [
                "Add multi-language support (Hindi, Arabic, Spanish, etc.)",
                "Include visual diagrams for wound care instructions",
                "Add text-to-speech audio generation",
                "Support health literacy assessment integration",
                "Add QR code for patient portal access"
            ],
            "next_step": "workflow_complete"
        }
    except Exception as e:
        logger.error(f"Patient Translator error: {e}")
        return {
            "module": "patient_translator",
            "module_output": {},
            "validation": {
                "schema_valid": False,
                "missing_fields": [],
                "logic_issues": [f"AI processing failed: {str(e)}"],
                "safety_flags": ["Translator unavailable — provide standard printed discharge instructions"]
            },
            "test_cases": [],
            "improvements": [],
            "next_step": "manual_patient_education"
        }


def _build_translator_prompt(
    clinical_content: dict[str, Any],
    patient: dict[str, Any] | None,
    target_language: str,
    reading_level: str,
) -> str:
    """Build Translator prompt."""
    parts = []
    
    if patient:
        name = patient.get("name", patient.get("first_name", "the patient"))
        parts.append(f"PATIENT NAME: {name}")
        parts.append(f"AGE: {patient.get('age', 'unknown')}")
    
    parts.append(f"TARGET LANGUAGE: {target_language}")
    parts.append(f"READING LEVEL: {reading_level}")
    
    # Handle different types of clinical content
    if "soap_note" in clinical_content:
        soap = clinical_content["soap_note"]
        assessment = soap.get("assessment", {})
        plan = soap.get("plan", {})
        parts.append(f"\nDIAGNOSIS: {assessment.get('primary_diagnosis', {}).get('description', 'N/A')}")
        parts.append(f"CLINICAL REASONING: {assessment.get('clinical_reasoning', '')}")
        parts.append(f"TREATMENT PLAN: {plan.get('summary', '')}")
        parts.append(f"FOLLOW-UP: {plan.get('follow_up', '')}")
    
    if "suggested_orders" in clinical_content:
        orders = clinical_content["suggested_orders"]
        meds = orders.get("medications", [])
        if meds:
            parts.append("\nMEDICATIONS PRESCRIBED:")
            for med in meds:
                parts.append(f"  - {med.get('drug', '')} {med.get('dose', '')} {med.get('route', '')} {med.get('frequency', '')} for {med.get('duration', '')}")
    
    if "discharge_summary" in clinical_content:
        parts.append(f"\nDISCHARGE SUMMARY:\n{clinical_content['discharge_summary']}")
    
    if "clinical_note" in clinical_content:
        parts.append(f"\nCLINICAL NOTE:\n{clinical_content['clinical_note']}")
    
    return "\n".join(parts)


def _validate_translator_output(result: dict) -> dict:
    """Validate Translator output."""
    missing = []
    issues = []
    safety_flags = []
    
    if "patient_summary" not in result:
        missing.append("patient_summary")
    if "care_instructions" not in result:
        missing.append("care_instructions")
    if "warning_signs" not in result:
        missing.append("warning_signs")
    
    # Check readability
    reading_level = result.get("reading_level", "")
    if reading_level not in ["grade_5", "grade_8"]:
        issues.append(f"Reading level '{reading_level}' may be too complex for average patients")
    
    # Ensure warning signs are included
    warnings = result.get("warning_signs", [])
    if not warnings:
        safety_flags.append("No warning signs included — patient may not know when to seek help")
    
    # Check medication instructions
    meds = result.get("medications_explained", [])
    for med in meds:
        if not med.get("when_to_call_doctor"):
            safety_flags.append(f"Missing 'when to call doctor' for {med.get('medicine_name', 'unknown')}")
    
    return {
        "schema_valid": len(missing) == 0,
        "missing_fields": missing,
        "logic_issues": issues,
        "safety_flags": safety_flags,
    }


def _generate_test_cases() -> list[dict]:
    return [
        {
            "name": "Discharge with medications",
            "input": {"discharge_summary": "Dx: Community-acquired pneumonia. Rx: Azithromycin 500mg x5d"},
            "expected_behavior": "Patient-friendly explanation of pneumonia, simple med instructions, warning signs"
        },
        {
            "name": "Edge case — complex multi-drug regimen",
            "input": {"medications": [{"drug": "Metformin"}, {"drug": "Lisinopril"}, {"drug": "Atorvastatin"}]},
            "expected_behavior": "Simple explanation of each drug with timing chart"
        },
        {
            "name": "Failure case — surgical discharge",
            "input": {"discharge_summary": "s/p laparoscopic cholecystectomy"},
            "expected_behavior": "Explain surgery in simple terms, wound care, activity restrictions"
        },
    ]
