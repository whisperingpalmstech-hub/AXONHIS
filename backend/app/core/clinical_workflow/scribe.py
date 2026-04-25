"""
Module 2: Actionable Scribe — Smart Order Set & Documentation Engine.

Converts doctor narration + Navigator insights into:
- UI-ready checkbox order sets (Labs, Imaging, Meds, Monitoring, Procedures)
- Structured SOAP notes
- Protocol-driven clinical actions
Acts as clinical documentation specialist + order automation engine.
"""
import json
import logging
from typing import Any

from app.core.ai.grok_client import grok_json

logger = logging.getLogger(__name__)


SCRIBE_SYSTEM_PROMPT = """You are the Actionable Scribe Module — a clinical documentation specialist and order automation engine.

Your role is to convert doctor narration and Clinical Navigator insights into:
1. Smart Order Set (UI-ready, checkbox format)
2. Structured SOAP Note
3. Protocol-driven medical actions

PROCESSING LOGIC (follow these steps exactly):

STEP 1: PARSE DOCTOR NARRATION
Extract: confirmed findings (fever, chest pain), negations ("no cough"), intent ("start antibiotics", "rule out MI").

STEP 2: DETERMINE CLINICAL PROTOCOL
Map to: Chest Pain Protocol, Infection/Sepsis Protocol, Respiratory Distress, Routine Evaluation, Surgical, or Custom.
Use navigator focus_area + doctor narration keywords.

STEP 3: BUILD SMART ORDER SET
Each item MUST include: id, label, selected (true/false), editable (true), category, reason.
Categories: Lab, Imaging, Medication, Monitoring, Procedure.

STEP 4: SELECTION LOGIC (CRITICAL)
- Default protocol items → selected: true
- Doctor says "Add X" → selected: true
- Doctor says "No X" → selected: false
- risk_level=High → auto-include critical tests
- NEVER remove safety-critical items silently

STEP 5: GENERATE SOAP NOTE
- Subjective: patient-reported symptoms
- Objective: findings from doctor + navigator
- Assessment: likely diagnosis / differential
- Plan: orders + treatment direction

EDGE CASES:
- Minimal narration → fallback to navigator data
- Conflicting info → flag in validation
- Ambiguous → choose safest protocol

Return a JSON object with this EXACT structure:

{
  "order_set_name": "Protocol name (e.g., Chest Pain Protocol)",
  "protocol_detected": "chest_pain|infection_sepsis|respiratory|routine|surgical|custom",

  "items": [
    {
      "id": "unique_id (e.g., lab_cbc_001)",
      "label": "Human-readable label (e.g., Complete Blood Count)",
      "selected": true,
      "editable": true,
      "category": "Lab|Imaging|Medication|Monitoring|Procedure",
      "reason": "Why this is included",
      "priority": "stat|routine|prn",
      "dose": "if medication, include dose/route/frequency"
    }
  ],

  "priority_level": "Routine|Urgent|Emergency",

  "draft_soap": {
    "subjective": "Patient-reported symptoms in narrative form",
    "objective": "Clinical findings, vitals, exam results",
    "assessment": "Primary diagnosis with ICD-10, differentials",
    "plan": "Treatment plan with orders summary"
  },

  "icd10_codes": [
    {"code": "", "description": "", "type": "primary|secondary"}
  ],

  "clinical_alerts": [],
  "documentation_completeness": 0.0
}

HARD CONSTRAINTS:
- No unstructured output
- All 4 SOAP fields must be present
- No unsafe omissions in high-risk cases
- NEVER ignore doctor overrides
- IDs must be unique
- Labels must be human-readable
- Return valid JSON ONLY

SAFETY RULES:
- NEVER skip critical diagnostics in high-risk cases
- ALWAYS include reasoning per item
- Flag conflicts between doctor intent and safety requirements
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
        navigator_output: Output from Clinical Navigator (optional)
        system_context: Hospital protocols and formulary rules
    
    Returns:
        Smart order set + SOAP note + coding.
    """
    user_message = _build_scribe_prompt(patient, encounter, navigator_output, system_context)
    
    messages = [
        {"role": "system", "content": SCRIBE_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    
    try:
        result = await grok_json(messages, temperature=0.2, max_tokens=2500)
        validation = _validate_scribe_output(result, patient, encounter)
        
        return {
            "module": "actionable_scribe",
            "module_output": result,
            "validation": validation,
            "test_cases": _generate_test_cases(),
            "improvements": [
                "Add formulary-aware medication suggestions",
                "Integrate voice-to-text real-time transcription",
                "Support template-based documentation shortcuts",
                "Protocol refinement based on hospital-specific guidelines",
                "Better categorization with sub-categories"
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
    """Build the user prompt for the Scribe using the input contract."""
    parts = []
    
    # Doctor narration
    doctor_input = encounter.get("doctor_input", "") or encounter.get("narrative", "")
    if doctor_input:
        parts.append(f"DOCTOR NARRATION:\n{doctor_input}")
    else:
        parts.append("DOCTOR NARRATION: (empty — use navigator data as fallback)")
    
    # Navigator output
    if navigator_output:
        nav = navigator_output.get("module_output", {})
        if nav:
            parts.append(f"\nNAVIGATOR OUTPUT:")
            parts.append(f"  focus_area: {nav.get('focus_area', 'unknown')}")
            
            cs = nav.get("clinical_summary", {})
            if cs:
                parts.append(f"  primary_symptoms: {cs.get('primary_symptoms', [])}")
                conditions = cs.get("suspected_conditions", [])
                if conditions:
                    cond_str = ", ".join([f"{c.get('condition', '')} ({c.get('probability', 0)*100:.0f}%)" for c in conditions])
                    parts.append(f"  suspected_conditions: {cond_str}")
                parts.append(f"  risk_factors: {cs.get('risk_factors', [])}")
            
            parts.append(f"  risk_level: {nav.get('risk_level', 'unknown')}")
            parts.append(f"  context_flags: {nav.get('context_flags', [])}")
            parts.append(f"  red_flags: {nav.get('red_flags', [])}")
            
            triage = nav.get("triage", {})
            if triage:
                parts.append(f"  triage: {triage.get('level', '')} (severity {triage.get('severity_score', '?')})")
                parts.append(f"  primary_impression: {triage.get('primary_impression', '')}")
    
    # Patient context
    parts.append(f"\nPATIENT CONTEXT:")
    parts.append(f"  age: {patient.get('age', 'unknown')}")
    parts.append(f"  gender: {patient.get('gender', 'unknown')}")
    
    history = patient.get("history", [])
    parts.append(f"  known_conditions: {history if history else '[]'}")
    
    medications = patient.get("medications", [])
    parts.append(f"  medications: {medications if medications else '[]'}")
    
    allergies = patient.get("allergies", [])
    parts.append(f"  allergies: {allergies if allergies else '[]'}")
    
    # Vitals
    vitals = encounter.get("vitals", [])
    if vitals:
        vitals_str = ", ".join([f"{v.get('name', '')}: {v.get('value', '')}" for v in vitals])
        parts.append(f"  vitals: {vitals_str}")
    
    # Notes
    notes = encounter.get("notes", [])
    if notes:
        parts.append(f"  additional_notes: {'; '.join(notes)}")
    
    return "\n".join(parts)


def _validate_scribe_output(result: dict, patient: dict, encounter: dict) -> dict:
    """Validate Scribe output for safety, completeness, and logic."""
    missing = []
    issues = []
    safety_flags = []
    
    # Schema checks
    if "items" not in result:
        missing.append("items")
    if "draft_soap" not in result:
        missing.append("draft_soap")
    else:
        soap = result["draft_soap"]
        for section in ["subjective", "objective", "assessment", "plan"]:
            if section not in soap or not soap[section]:
                missing.append(f"draft_soap.{section}")
    
    if "order_set_name" not in result:
        missing.append("order_set_name")
    if "priority_level" not in result:
        missing.append("priority_level")
    
    # Order item validation
    items = result.get("items", [])
    ids = set()
    for item in items:
        item_id = item.get("id", "")
        if item_id in ids:
            issues.append(f"Duplicate order ID: {item_id}")
        ids.add(item_id)
        
        if not item.get("label"):
            issues.append(f"Missing label for order {item_id}")
        if not item.get("reason"):
            issues.append(f"Missing reason for order {item_id}")
        if item.get("category") not in ["Lab", "Imaging", "Medication", "Monitoring", "Procedure"]:
            issues.append(f"Invalid category '{item.get('category')}' for {item_id}")
    
    # Safety: check medications against allergies
    allergies = set(a.lower() for a in patient.get("allergies", []))
    for item in items:
        if item.get("category") == "Medication" and item.get("selected"):
            label = item.get("label", "").lower()
            for allergy in allergies:
                if allergy in label or label in allergy:
                    safety_flags.append(f"CRITICAL: Order '{item.get('label')}' may conflict with allergy '{allergy}'")
    
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
            "name": "Standard case — mild infection",
            "input": {
                "doctor_narration": "Patient has UTI symptoms, dysuria for 3 days, no fever. Start empiric antibiotics.",
                "navigator_output": {"focus_area": "Genitourinary", "risk_level": "Low"},
                "patient_context": {"age": "35", "gender": "Female", "allergies": []}
            },
            "expected_behavior": "Routine protocol, urinalysis+culture selected, antibiotic order, all SOAP fields present"
        },
        {
            "name": "High-risk case — chest pain + high risk",
            "input": {
                "doctor_narration": "Acute chest pain, ECG shows ST elevation. Start heparin drip, dual antiplatelet.",
                "navigator_output": {"focus_area": "Cardiovascular", "risk_level": "High"},
                "patient_context": {"age": "60", "gender": "Male", "allergies": ["Aspirin"]}
            },
            "expected_behavior": "Emergency Chest Pain Protocol, aspirin allergy flagged, troponin stat, cath lab alert"
        },
        {
            "name": "Conflict case — doctor says no test but risk demands it",
            "input": {
                "doctor_narration": "Chest pain, probably muscular. No need for troponin or ECG.",
                "navigator_output": {"focus_area": "Cardiovascular", "risk_level": "High", "red_flags": ["chest pain"]},
                "patient_context": {"age": "55", "allergies": []}
            },
            "expected_behavior": "clinical_alert flagging conflict: doctor declined troponin but risk_level=High demands it"
        },
    ]
