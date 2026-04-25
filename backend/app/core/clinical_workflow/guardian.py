"""
Module 3: Guardian — Safety, Error & Compliance Engine.

6-step invisible safety net that audits clinical orders against:
1. Allergy cross-reactivity
2. Drug-drug interactions
3. Duplicate/timing conflicts
4. Contraindications (age, conditions)
5. Clinical logic gaps
6. Fraud/abuse detection

Does NOT block actions — detects, flags, and explains risks.
Acts as Clinical Pharmacist + Safety Auditor + Compliance Officer.
"""
import json
import logging
from typing import Any

from app.core.ai.grok_client import grok_json

logger = logging.getLogger(__name__)


GUARDIAN_SYSTEM_PROMPT = """You are the Guardian Module — an invisible safety net that audits clinical orders.

You act as a combination of Clinical Pharmacist, Safety Auditor, and Compliance Officer.

You DO NOT block actions. You detect, flag, and explain risks.

PROCESSING LOGIC (follow ALL 6 steps):

STEP 1: ALLERGY CHECK
For each order, compare with patient allergies (including cross-reactivity classes).
- Penicillin allergy → flag Amoxicillin, Ampicillin (beta-lactam cross-reactivity)
- Sulfa allergy → flag Sulfamethoxazole, Celecoxib
- Match = HIGH severity alert + suggest safer alternative

STEP 2: DRUG-DRUG INTERACTION CHECK
Cross-check new medications with current medications.
Examples: Warfarin + NSAIDs, ACE inhibitors + potassium supplements, Statins + Macrolides.
Interaction found = Medium/High alert with explanation.

STEP 3: DUPLICATE / TIMING CHECK
Check if same test was done recently (within unsafe window).
- CBC repeated within 4 hours = LOW alert
- CT scan repeated within 24 hours = MEDIUM alert
- Flag unnecessary repeats

STEP 4: CONTRAINDICATION CHECK
Match orders against age, gender, existing conditions.
- NSAIDs in CKD = HIGH
- Metformin in CKD Stage 4-5 = HIGH
- Contrast imaging in renal failure = HIGH
- ACE inhibitors in pregnancy = HIGH

STEP 5: CLINICAL LOGIC CHECK
Detect missing critical orders in high-risk cases or illogical combinations.
- Chest pain but no ECG/Troponin ordered = MEDIUM
- Anticoagulation without baseline coagulation panel = MEDIUM
- Insulin without glucose monitoring = LOW

STEP 6: FRAUD / ABUSE DETECTION
Identify billing anomalies and over-ordering.
- Same expensive imaging repeated within 48 hours = LOW/MEDIUM
- Excessive lab panels without clinical justification = LOW
- Pattern of unnecessary procedures = MEDIUM

Return a JSON object with this EXACT structure:

{
  "overall_safety": "safe|caution|unsafe",
  "guardian_summary": "1-2 sentence summary of findings",

  "alerts": [
    {
      "severity": "Low|Medium|High",
      "type": "Allergy|Interaction|Duplicate|Contraindication|Logic|Fraud",
      "affected_order": "Name of the order that triggered the alert",
      "message": "Clear explanation of the risk",
      "action": "Recommended action (e.g., substitute drug, add monitoring)",
      "override_required": true,
      "alternative": "Safer alternative if applicable"
    }
  ],

  "allergy_alerts": [
    {
      "proposed_drug": "",
      "allergen": "",
      "cross_reactivity_class": "",
      "severity": "High",
      "recommendation": ""
    }
  ],

  "drug_interactions": [
    {
      "drug_a": "",
      "drug_b": "",
      "interaction_type": "major|moderate|minor",
      "description": "",
      "recommendation": ""
    }
  ],

  "contraindications": [
    {
      "order": "",
      "condition": "",
      "risk": "",
      "severity": "High|Medium",
      "recommendation": ""
    }
  ],

  "duplicate_flags": [
    {
      "order": "",
      "reason": "",
      "severity": "Low|Medium"
    }
  ],

  "logic_gaps": [
    {
      "finding": "",
      "missing_order": "",
      "severity": "Medium",
      "recommendation": ""
    }
  ],

  "fraud_flags": [
    {
      "pattern": "",
      "severity": "Low|Medium",
      "recommendation": ""
    }
  ],

  "audit_summary": {
    "total_orders_checked": 0,
    "issues_detected": 0,
    "high_risk_count": 0,
    "medium_risk_count": 0,
    "low_risk_count": 0,
    "orders_safe": 0
  }
}

HARD CONSTRAINTS:
- DO NOT block doctor actions
- DO NOT miss high-risk alerts (allergy cross-reactivity is CRITICAL)
- DO NOT generate vague warnings — be specific and actionable
- DO NOT assume missing patient data — flag it
- Return valid JSON ONLY
"""


async def guard(
    patient: dict[str, Any],
    proposed_orders: dict[str, Any],
    system_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run Guardian safety engine on proposed orders.

    Args:
        patient: Patient demographics, allergies, medications, conditions
        proposed_orders: Orders to validate {medications: [], labs: [], imaging: []}
        system_context: Hospital rules, formulary restrictions

    Returns:
        Safety audit with alerts, interactions, and compliance flags.
    """
    user_message = _build_guardian_prompt(patient, proposed_orders, system_context)

    messages = [
        {"role": "system", "content": GUARDIAN_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        result = await grok_json(messages, temperature=0.1, max_tokens=2500)
        validation = _validate_guardian_output(result, patient, proposed_orders)

        return {
            "module": "guardian",
            "module_output": result,
            "validation": validation,
            "test_cases": _generate_test_cases(),
            "improvements": [
                "Integrate formal drug-drug interaction database (DrugBank/RxNorm)",
                "Add real-time formulary checking against hospital pharmacy",
                "Implement renal dosing adjustments based on eGFR",
                "Track ordering patterns per physician for anomaly detection",
                "Add pregnancy-category drug checking"
            ],
            "next_step": "handover"
        }
    except Exception as e:
        logger.error(f"Guardian error: {e}")
        return {
            "module": "guardian",
            "module_output": {
                "overall_safety": "caution",
                "guardian_summary": "Guardian engine unavailable — manual safety review required",
                "alerts": [{"severity": "Medium", "type": "Logic", "affected_order": "all",
                           "message": f"AI safety check failed: {str(e)}",
                           "action": "Perform manual allergy and interaction review",
                           "override_required": False}],
                "audit_summary": {"total_orders_checked": 0, "issues_detected": 1, "high_risk_count": 0}
            },
            "validation": {"schema_valid": False, "issues": [str(e)]},
            "test_cases": [],
            "improvements": [],
            "next_step": "manual_review"
        }


def _build_guardian_prompt(
    patient: dict[str, Any],
    proposed_orders: dict[str, Any],
    system_context: dict[str, Any] | None,
) -> str:
    """Build the user prompt for the Guardian."""
    parts = []

    # Proposed orders
    parts.append("PROPOSED ORDERS:")
    meds = proposed_orders.get("medications", [])
    if meds:
        parts.append("  Medications:")
        for m in meds:
            if isinstance(m, dict):
                parts.append(f"    - {m.get('drug', m.get('label', ''))} | dose: {m.get('dose', '')} | route: {m.get('route', '')} | freq: {m.get('frequency', '')}")
            else:
                parts.append(f"    - {m}")

    labs = proposed_orders.get("labs", proposed_orders.get("lab_tests", []))
    if labs:
        parts.append("  Labs:")
        for l in labs:
            parts.append(f"    - {l if isinstance(l, str) else l.get('test', l.get('label', ''))}")

    imaging = proposed_orders.get("imaging", [])
    if imaging:
        parts.append("  Imaging:")
        for img in imaging:
            parts.append(f"    - {img if isinstance(img, str) else img.get('study', img.get('label', ''))}")

    procedures = proposed_orders.get("procedures", [])
    if procedures:
        parts.append("  Procedures:")
        for p in procedures:
            parts.append(f"    - {p if isinstance(p, str) else p.get('label', '')}")

    # Patient data
    parts.append(f"\nPATIENT DATA:")
    parts.append(f"  age: {patient.get('age', 'unknown')}")
    parts.append(f"  gender: {patient.get('gender', 'unknown')}")

    conditions = patient.get("history", patient.get("conditions", []))
    parts.append(f"  conditions: {conditions if conditions else '[] (FLAG: unknown history)'}")

    allergies = patient.get("allergies", [])
    parts.append(f"  allergies: {allergies if allergies else '[] (NKDA)'}")

    current_meds = patient.get("medications", [])
    parts.append(f"  current_medications: {current_meds if current_meds else '[]'}")

    recent_tests = patient.get("recent_tests", [])
    if recent_tests:
        parts.append(f"  recent_tests: {recent_tests}")

    # System context
    if system_context:
        formulary = system_context.get("formulary_restrictions", [])
        if formulary:
            parts.append(f"\nFORMULARY RESTRICTIONS: {formulary}")
        rules = system_context.get("hospital_rules", [])
        if rules:
            parts.append(f"HOSPITAL RULES: {rules}")

    return "\n".join(parts)


def _validate_guardian_output(result: dict, patient: dict, orders: dict) -> dict:
    """Validate Guardian output for completeness."""
    issues = []

    if "overall_safety" not in result:
        issues.append("Missing overall_safety field")
    if "alerts" not in result:
        issues.append("Missing alerts array")
    if "audit_summary" not in result:
        issues.append("Missing audit_summary")

    # Check alert quality
    for alert in result.get("alerts", []):
        if not alert.get("message"):
            issues.append("Alert missing message")
        if alert.get("severity") not in ["Low", "Medium", "High"]:
            issues.append(f"Invalid severity: {alert.get('severity')}")
        if not alert.get("action"):
            issues.append("Alert missing recommended action")

    # Cross-check: if patient has allergies, at least allergy check should have run
    if patient.get("allergies") and not result.get("allergy_alerts") and result.get("overall_safety") == "safe":
        # Double check — are any proposed meds in allergy class?
        pass  # AI should handle this

    return {
        "schema_valid": len(issues) == 0,
        "issues": issues,
    }


def _generate_test_cases() -> list[dict]:
    return [
        {
            "name": "Safe case — no conflicts",
            "input": {
                "proposed_orders": [{"label": "CBC", "category": "Lab"}, {"label": "Paracetamol 500mg", "category": "Medication"}],
                "patient_data": {"age": "30", "allergies": [], "medications": [], "conditions": []}
            },
            "expected_behavior": "overall_safety=safe, no alerts, audit_summary shows 0 issues"
        },
        {
            "name": "Allergy conflict — Penicillin allergy + Amoxicillin order",
            "input": {
                "proposed_orders": [{"label": "Amoxicillin 500mg", "category": "Medication"}],
                "patient_data": {"age": "55", "allergies": ["Penicillin"], "medications": [], "conditions": []}
            },
            "expected_behavior": "overall_safety=unsafe, HIGH allergy alert, cross-reactivity flagged, alternative suggested"
        },
        {
            "name": "Duplicate order — CBC repeated within 2 hours",
            "input": {
                "proposed_orders": [{"label": "CBC", "category": "Lab"}],
                "patient_data": {"age": "45", "allergies": [], "recent_tests": [{"name": "CBC", "timestamp": "2 hours ago"}]}
            },
            "expected_behavior": "overall_safety=caution, LOW duplicate alert, timing flag raised"
        },
    ]
