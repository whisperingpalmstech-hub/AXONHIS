"""
Module 5: Patient Translator — Human-Friendly Clinical Communication.

Converts medical jargon into patient-friendly language at grade 5 reading level.
Produces structured output for the Patient Portal with:
- Simple summary (what happened, what we found, what to do)
- Medication instructions with warnings
- Warning signs (when to go to ER vs call doctor)
- Care instructions by category
- FAQ section
"""
import json
import logging
from typing import Any

from app.core.ai.grok_client import grok_json

logger = logging.getLogger(__name__)


TRANSLATOR_SYSTEM_PROMPT = """You are the Patient Translator — you convert medical language into simple, warm, human-friendly communication.

TARGET: Grade 5 reading level. The patient may have no medical background.

RULES:
- Use short sentences (max 15 words each)
- Replace ALL medical terms with plain language
- Use analogies where helpful (e.g., "stent" = "a tiny tube to keep the blood vessel open")
- Be warm and reassuring but honest
- Use "you/your" language, not third person
- Include emoji for visual scanning

Return a JSON object with this EXACT structure:

{
  "patient_summary": {
    "title": "Short friendly title (e.g., Your Recovery Plan)",
    "what_happened": "Simple explanation of what the doctor did/found",
    "what_we_found": "Key findings in plain language",
    "what_it_means": "What this means for the patient",
    "what_to_do_next": "Clear next steps"
  },

  "medications": [
    {
      "name": "Drug name",
      "simple_name": "What it does in simple words",
      "how_to_take": "Clear instructions (e.g., Take 1 pill every morning with food)",
      "why": "Why you need this medicine",
      "warnings": ["Don't take with alcohol", "May cause drowsiness"],
      "icon": "💊"
    }
  ],

  "warning_signs": [
    {
      "sign": "What to watch for",
      "urgency": "call_911|go_to_er|call_doctor|watch",
      "action": "What to do if this happens",
      "icon": "🚨"
    }
  ],

  "care_instructions": [
    {
      "category": "diet|activity|wound_care|hygiene|mental_health",
      "instruction": "Simple instruction",
      "priority": "must_do|recommended|optional",
      "icon": "🍎"
    }
  ],

  "follow_up": {
    "when": "When to come back (e.g., In 2 weeks)",
    "where": "Which department/clinic",
    "what_to_bring": "List of things to bring",
    "questions_to_ask": ["Suggested questions for the doctor"]
  },

  "faq": [
    {
      "question": "Common patient question",
      "answer": "Simple, reassuring answer"
    }
  ],

  "reading_level": "grade_5",
  "language": "en"
}

HARD CONSTRAINTS:
- NO medical jargon in output (no ICD codes, no Latin terms)
- NO scary language — be honest but reassuring
- EVERY medication must have how_to_take and warnings
- Warning signs must be sorted by urgency (most urgent first)
- Return valid JSON ONLY
"""


async def translate(
    clinical_content: dict[str, Any],
    patient: dict[str, Any] | None = None,
    target_language: str = "en",
    reading_level: str = "grade_5",
) -> dict[str, Any]:
    """
    Translate clinical content into patient-friendly format.

    Args:
        clinical_content: Clinical data (SOAP notes, orders, discharge summary)
        patient: Patient demographics for personalization
        target_language: Target language code
        reading_level: Target reading level

    Returns:
        Patient-friendly structured communication.
    """
    user_message = _build_translator_prompt(clinical_content, patient, target_language, reading_level)

    messages = [
        {"role": "system", "content": TRANSLATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        result = await grok_json(messages, temperature=0.3, max_tokens=2500)
        validation = _validate_translator_output(result)

        return {
            "module": "patient_translator",
            "module_output": result,
            "validation": validation,
            "improvements": [
                "Add multi-language support (Hindi, Arabic, Spanish)",
                "Include audio read-aloud generation",
                "Add visual diagrams for procedures",
                "Personalize reading level based on patient profile",
                "Add cultural sensitivity filters"
            ],
            "next_step": "patient_portal"
        }
    except Exception as e:
        logger.error(f"Translator error: {e}")
        return {
            "module": "patient_translator",
            "module_output": {},
            "validation": {"schema_valid": False, "issues": [str(e)]},
            "improvements": [],
            "next_step": "manual_translation"
        }


def _build_translator_prompt(
    clinical_content: dict[str, Any],
    patient: dict[str, Any] | None,
    target_language: str,
    reading_level: str,
) -> str:
    """Build the user prompt for the Translator."""
    parts = []

    # Patient context
    if patient:
        name = patient.get("name", "")
        age = patient.get("age", "")
        gender = patient.get("gender", "")
        if name:
            parts.append(f"PATIENT: {name} ({age}y, {gender})")
        else:
            parts.append(f"PATIENT: Age {age}, Gender {gender}")

    parts.append(f"TARGET LANGUAGE: {target_language}")
    parts.append(f"READING LEVEL: {reading_level}")

    # Clinical content
    parts.append(f"\nCLINICAL CONTENT TO TRANSLATE:")

    # Handle different input formats
    if isinstance(clinical_content, str):
        parts.append(clinical_content)
    elif isinstance(clinical_content, dict):
        # SOAP note
        soap = clinical_content.get("draft_soap", {})
        if soap:
            parts.append(f"  SOAP Note:")
            parts.append(f"    Subjective: {soap.get('subjective', '')}")
            parts.append(f"    Objective: {soap.get('objective', '')}")
            parts.append(f"    Assessment: {soap.get('assessment', '')}")
            parts.append(f"    Plan: {soap.get('plan', '')}")

        # Orders
        items = clinical_content.get("items", [])
        if items:
            meds = [i for i in items if i.get("category") == "Medication" and i.get("selected")]
            if meds:
                parts.append(f"  Medications ordered:")
                for m in meds:
                    parts.append(f"    - {m.get('label', '')} {m.get('dose', '')}")

            labs = [i for i in items if i.get("category") == "Lab" and i.get("selected")]
            if labs:
                parts.append(f"  Lab tests ordered:")
                for l in labs:
                    parts.append(f"    - {l.get('label', '')}")

        # ICD codes
        codes = clinical_content.get("icd10_codes", [])
        if codes:
            parts.append(f"  Diagnoses:")
            for c in codes:
                parts.append(f"    - {c.get('code', '')}: {c.get('description', '')}")

        # Discharge summary (direct text)
        discharge = clinical_content.get("discharge_summary", clinical_content.get("clinical_narrative", ""))
        if discharge:
            parts.append(f"  Clinical Summary: {discharge}")

        # Any raw text content
        content = clinical_content.get("content", clinical_content.get("text", ""))
        if content:
            parts.append(f"  Content: {content}")

    return "\n".join(parts)


def _validate_translator_output(result: dict) -> dict:
    """Validate Translator output."""
    issues = []

    if "patient_summary" not in result:
        issues.append("Missing patient_summary")
    else:
        ps = result["patient_summary"]
        for field in ["title", "what_happened", "what_to_do_next"]:
            if field not in ps or not ps[field]:
                issues.append(f"Missing patient_summary.{field}")

    # Check medications have required fields
    for med in result.get("medications", []):
        if not med.get("how_to_take"):
            issues.append(f"Medication '{med.get('name', '?')}' missing how_to_take")
        if not med.get("warnings"):
            issues.append(f"Medication '{med.get('name', '?')}' missing warnings")

    # Check warning signs are sorted by urgency
    urgency_order = {"call_911": 0, "go_to_er": 1, "call_doctor": 2, "watch": 3}
    signs = result.get("warning_signs", [])
    for i in range(len(signs) - 1):
        curr = urgency_order.get(signs[i].get("urgency", ""), 99)
        nxt = urgency_order.get(signs[i + 1].get("urgency", ""), 99)
        if curr > nxt:
            issues.append("Warning signs not sorted by urgency (most urgent should be first)")
            break

    # Jargon check (basic)
    text = json.dumps(result).lower()
    jargon_terms = ["myocardial infarction", "percutaneous", "etiology", "prognosis",
                     "contraindicated", "prophylaxis", "sequelae", "comorbidity"]
    for term in jargon_terms:
        if term in text:
            issues.append(f"Medical jargon detected: '{term}' — should be simplified")

    return {
        "schema_valid": len(issues) == 0,
        "issues": issues,
    }
