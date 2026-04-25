"""
Module 1: Clinical Navigator — Guided Discovery & Intake Intelligence Engine.

Analyzes patient symptoms → extracts clinical signals → maps body system →
cross-checks history → stratifies risk → generates guided questions +
exam suggestions + context flags. Acts as senior triage physician + diagnostic strategist.
"""
import json
import logging
from typing import Any

from app.core.ai.grok_client import grok_json

logger = logging.getLogger(__name__)


NAVIGATOR_SYSTEM_PROMPT = """You are the Clinical Navigator Module — a senior triage physician and diagnostic strategist AI.

Your role is to guide the doctor during patient intake by:
- Interpreting patient narration
- Cross-checking medical history
- Identifying risks and missing information
- Suggesting next best clinical questions and exams

PROCESSING LOGIC (follow these steps exactly):

STEP 1: EXTRACT CLINICAL SIGNALS
From the narrative, identify: primary symptoms, duration, severity indicators, associated symptoms, risk factors (age, history).

STEP 2: SYSTEM MAPPING
Map symptoms to: Cardiovascular, Respiratory, Neurological, Gastrointestinal, Musculoskeletal, Endocrine, or General/Unknown.

STEP 3: CONTEXT CROSS-CHECK (CRITICAL)
Compare narrative vs history. Identify: missing links (important symptoms not mentioned), risk amplifiers (e.g., diabetes + infection), contradictions.

STEP 4: RISK STRATIFICATION
- Low → Mild symptoms, no risk history
- Medium → Symptoms + moderate risk factors
- High → Red flags or dangerous comorbid history

STEP 5: GENERATE GUIDED QUESTIONS (MAX 4)
High diagnostic value, no redundancy, prioritize life-threatening exclusions.
Types: symptom clarification, timeline probing, risk exposure, red flag screening.

STEP 6: SUGGEST PHYSICAL EXAMS (2-4)
Relevant to suspected system, practical in real clinical setting.

STEP 7: CONTEXT FLAGS
Generate alerts: recent hospitalization, high-risk comorbidity, symptom mismatch, missing data.

EDGE CASES:
- Vague narrative → ask clarifying questions, reduce confidence
- Empty narrative → return structured prompt requesting input
- Contradictory info → flag inconsistency
- Missing history → add validation warning, reduce confidence

Return a JSON object with this EXACT structure:

{
  "focus_area": "Primary body system affected",

  "clinical_summary": {
    "primary_symptoms": [],
    "suspected_conditions": [
      {"condition": "", "icd10": "", "probability": 0.0, "reasoning": ""}
    ],
    "risk_factors": []
  },

  "triage": {
    "level": "ESI-1|ESI-2|ESI-3|ESI-4|ESI-5",
    "color": "red|orange|yellow|green|blue",
    "severity_score": 1-10,
    "primary_impression": "Most likely diagnosis"
  },

  "red_flags": [],

  "ask_next": [
    "Question 1 — highest diagnostic value",
    "Question 2",
    "Question 3",
    "Question 4"
  ],

  "suggested_exam": [
    "Physical exam 1 with rationale",
    "Physical exam 2 with rationale"
  ],

  "context_flags": [
    "Flag about history, risks, or missing data"
  ],

  "recommended_routing": {
    "department": "",
    "urgency": "immediate|urgent|semi_urgent|routine",
    "specialist": ""
  },

  "recommended_workup": {
    "labs": [],
    "imaging": [],
    "procedures": []
  },

  "risk_level": "Low|Medium|High",
  "confidence_score": 0.0,
  "clinical_narrative": "2-3 sentence clinical reasoning summary"
}

HARD CONSTRAINTS:
- Do NOT exceed 4 questions in ask_next
- Do NOT hallucinate or assume history not provided
- Do NOT ignore risk factors
- Do NOT output unstructured text
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
        Structured guided discovery + triage output.
    """
    user_message = _build_navigator_prompt(patient, encounter, system_context)
    
    messages = [
        {"role": "system", "content": NAVIGATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    
    try:
        result = await grok_json(messages, temperature=0.2, max_tokens=2000)
        
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
                "Add NEWS2/MEWS scoring integration",
                "Better questioning strategies based on symptom clusters",
                "Missing clinical signals detection via NLP"
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
    """Build the user prompt for the Navigator using the input contract."""
    parts = []
    
    # Patient narrative
    narrative = encounter.get("narrative", "") or encounter.get("doctor_input", "")
    if narrative:
        parts.append(f"PATIENT NARRATIVE: {narrative}")
    else:
        parts.append("PATIENT NARRATIVE: (empty — request structured input from doctor)")

    # Patient history block
    parts.append("\nPATIENT HISTORY:")
    
    # Demographics
    parts.append(f"  Age: {patient.get('age', 'unknown')}")
    parts.append(f"  Gender: {patient.get('gender', 'unknown')}")
    
    # Conditions / PMH
    history = patient.get("history", [])
    if history:
        parts.append(f"  Conditions: {', '.join(history)}")
    else:
        parts.append("  Conditions: [] (FLAG: no history provided — incomplete)")
    
    # Surgeries
    surgeries = patient.get("surgeries", [])
    if surgeries:
        parts.append(f"  Surgeries: {', '.join(surgeries)}")
    
    # Medications
    medications = patient.get("medications", [])
    if medications:
        parts.append(f"  Medications: {', '.join(medications)}")
    else:
        parts.append("  Medications: [] (FLAG: no medications reported)")
    
    # Allergies
    allergies = patient.get("allergies", [])
    if allergies:
        parts.append(f"  Allergies: {', '.join(allergies)}")
    else:
        parts.append("  Allergies: NKDA")
    
    # Recent visits
    recent_visits = patient.get("recent_visits", [])
    if recent_visits:
        parts.append(f"  Recent Visits: {', '.join(recent_visits)}")
    
    # Vitals
    vitals = encounter.get("vitals", [])
    if vitals:
        vitals_str = ", ".join([f"{v.get('name', '')}: {v.get('value', '')}" for v in vitals])
        parts.append(f"\nVITALS: {vitals_str}")
    else:
        parts.append("\nVITALS: Not recorded (FLAG: vitals missing)")
    
    # Notes
    notes = encounter.get("notes", [])
    if notes:
        parts.append(f"ADDITIONAL NOTES: {'; '.join(notes)}")
    
    # System context
    if system_context:
        protocols = system_context.get("protocols", [])
        if protocols:
            parts.append(f"HOSPITAL PROTOCOLS: {', '.join(protocols)}")
    
    return "\n".join(parts)


def _validate_navigator_output(result: dict, patient: dict) -> dict:
    """Validate the Navigator output for safety, completeness, and logic."""
    missing = []
    issues = []
    safety_flags = []
    
    # Schema checks — new fields
    required_fields = [
        "focus_area", "clinical_summary", "triage", "ask_next",
        "suggested_exam", "risk_level", "confidence_score"
    ]
    for field in required_fields:
        if field not in result:
            missing.append(field)
    
    # Also accept legacy format
    if "triage_level" in result and "triage" not in result:
        result["triage"] = {
            "level": result.get("triage_level", ""),
            "color": result.get("triage_color", ""),
            "severity_score": result.get("severity_score", 0),
            "primary_impression": result.get("primary_impression", ""),
        }
        missing = [m for m in missing if m != "triage"]
    
    # Question quality check
    questions = result.get("ask_next", [])
    if len(questions) > 4:
        issues.append(f"Too many questions ({len(questions)}) — max 4 allowed")
    
    # Risk level logic
    triage = result.get("triage", {})
    severity = triage.get("severity_score", 0) if isinstance(triage, dict) else 0
    risk_level = result.get("risk_level", "")
    
    if severity >= 8 and risk_level == "Low":
        issues.append(f"Severity {severity} but risk_level=Low — mismatch")
    if severity <= 3 and risk_level == "High":
        issues.append(f"Severity {severity} but risk_level=High — verify")
    
    # Confidence check
    confidence = result.get("confidence_score", 0)
    if confidence < 0.5:
        safety_flags.append(f"Low confidence ({confidence:.0%}) — clinical judgment needed")
    
    # Red flags check
    red_flags = result.get("red_flags", [])
    triage_level = triage.get("level", "") if isinstance(triage, dict) else ""
    if red_flags and triage_level not in ["ESI-1", "ESI-2", "ESI-3"]:
        safety_flags.append("Red flags present but triage level may be too low")
    
    # Context flags check
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
            "name": "Normal case — fever with cough",
            "input": {
                "patient_narrative": "Low grade fever for 3 days with dry cough",
                "patient_history": {"conditions": [], "medications": [], "allergies": []}
            },
            "expected_behavior": "focus_area=Respiratory, risk_level=Low, 3-4 clarifying questions, chest exam suggested"
        },
        {
            "name": "High-risk case — chest pain + cardiac history",
            "input": {
                "patient_narrative": "Crushing chest pain for 30 minutes radiating to arm",
                "patient_history": {"conditions": ["MI 2022", "Hypertension"], "medications": ["Aspirin 81mg"]}
            },
            "expected_behavior": "focus_area=Cardiovascular, risk_level=High, ESI-1, red flags flagged, immediate cardiology routing"
        },
        {
            "name": "Edge case — vague/empty narrative",
            "input": {
                "patient_narrative": "Not feeling well",
                "patient_history": {"conditions": []}
            },
            "expected_behavior": "Low confidence, clarifying questions generated, context_flags about missing data"
        },
    ]
