"""
Module 3: Guardian — Safety & Compliance Validation Engine.

Validates all orders against patient safety rules: allergies, drug interactions,
contraindications, dosage limits, and hospital protocols.
"""
import json
import logging
from typing import Any

from app.core.ai.grok_client import grok_json

logger = logging.getLogger(__name__)


GUARDIAN_SYSTEM_PROMPT = """You are a Clinical Guardian AI — an expert patient safety and compliance validation system.

Given a set of proposed orders and the patient's complete profile, you MUST validate each order and return a JSON object with this EXACT structure:

{
  "overall_safety": "safe|caution|unsafe",
  "overall_risk_score": 0-10,
  "order_validations": [
    {
      "order_id": "",
      "order_description": "",
      "status": "approved|warning|blocked",
      "severity": "info|low|medium|high|critical",
      "alerts": [
        {
          "type": "allergy|interaction|contraindication|dosage|duplicate|protocol",
          "message": "",
          "severity": "info|warning|critical",
          "evidence": "",
          "recommendation": ""
        }
      ],
      "override_allowed": true,
      "override_requires": "attending|pharmacist|none"
    }
  ],
  "drug_interactions": [
    {
      "drug_a": "",
      "drug_b": "",
      "interaction_type": "major|moderate|minor",
      "description": "",
      "clinical_significance": "",
      "recommendation": ""
    }
  ],
  "allergy_alerts": [
    {
      "allergen": "",
      "proposed_drug": "",
      "cross_reactivity": true,
      "severity": "mild|moderate|severe|anaphylaxis",
      "recommendation": ""
    }
  ],
  "dosage_checks": [
    {
      "drug": "",
      "proposed_dose": "",
      "max_recommended": "",
      "patient_factors": [],
      "adjustment_needed": true,
      "recommendation": ""
    }
  ],
  "compliance_flags": [
    {
      "rule": "",
      "status": "compliant|non_compliant",
      "action_required": ""
    }
  ],
  "guardian_summary": ""
}

RULES:
- NEVER approve a known allergy match without critical alert
- Flag ALL drug-drug interactions
- Check dosage against age, weight, renal/hepatic function
- Apply hospital formulary restrictions if provided
- Mark duplicate orders
- Return valid JSON ONLY
"""


async def guard(
    patient: dict[str, Any],
    proposed_orders: dict[str, Any],
    system_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run Guardian safety validation on proposed orders.
    
    Args:
        patient: Patient profile with allergies, medications, history
        proposed_orders: Orders from Scribe or manual entry
        system_context: Hospital formulary and protocol rules
    
    Returns:
        Safety validation results with alerts and recommendations.
    """
    user_message = _build_guardian_prompt(patient, proposed_orders, system_context)
    
    messages = [
        {"role": "system", "content": GUARDIAN_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    
    try:
        result = await grok_json(messages, temperature=0.1, max_tokens=2000)
        
        # Run local rule-based checks too (defense in depth)
        local_alerts = _run_local_safety_checks(patient, proposed_orders)
        
        # Merge local alerts into AI result
        if local_alerts:
            existing_allergy_alerts = result.get("allergy_alerts", [])
            existing_allergy_alerts.extend(local_alerts.get("allergy_alerts", []))
            result["allergy_alerts"] = existing_allergy_alerts
            
            if local_alerts.get("has_critical"):
                result["overall_safety"] = "unsafe"
        
        validation = _validate_guardian_output(result)
        
        return {
            "module": "guardian",
            "module_output": result,
            "validation": validation,
            "test_cases": _generate_test_cases(),
            "improvements": [
                "Integrate real pharmacology database for interaction checking",
                "Add renal/hepatic dosing adjustments",
                "Support pediatric weight-based dosing validation",
                "Add pregnancy category checking"
            ],
            "next_step": "handover_engine"
        }
    except Exception as e:
        logger.error(f"Guardian error: {e}")
        return {
            "module": "guardian",
            "module_output": {
                "overall_safety": "unknown",
                "overall_risk_score": 10,
                "guardian_summary": "Guardian AI unavailable — MANUAL safety review required"
            },
            "validation": {
                "schema_valid": False,
                "missing_fields": [],
                "logic_issues": [f"AI processing failed: {str(e)}"],
                "safety_flags": ["CRITICAL: Guardian unavailable — all orders require manual pharmacist review"]
            },
            "test_cases": [],
            "improvements": [],
            "next_step": "manual_safety_review"
        }


def _run_local_safety_checks(patient: dict, proposed_orders: dict) -> dict:
    """Run deterministic local safety checks (no AI needed)."""
    alerts = {"allergy_alerts": [], "has_critical": False}
    
    allergies = [a.lower().strip() for a in patient.get("allergies", [])]
    current_meds = [m.lower().strip() for m in patient.get("medications", [])]
    
    # Check medications against allergies
    meds = proposed_orders.get("medications", [])
    for med in meds:
        drug = med.get("drug", "").lower()
        
        # Direct allergy match
        for allergy in allergies:
            if allergy in drug or drug in allergy:
                alerts["allergy_alerts"].append({
                    "allergen": allergy,
                    "proposed_drug": med.get("drug", ""),
                    "cross_reactivity": False,
                    "severity": "anaphylaxis",
                    "recommendation": f"DO NOT administer {med.get('drug')} — patient allergic to {allergy}"
                })
                alerts["has_critical"] = True
        
        # Penicillin cross-reactivity
        penicillin_drugs = ["amoxicillin", "ampicillin", "piperacillin", "penicillin"]
        cephalosporin_drugs = ["cephalexin", "ceftriaxone", "cefazolin", "cefuroxime"]
        
        if any(a in ["penicillin", "amoxicillin"] for a in allergies):
            if any(c in drug for c in cephalosporin_drugs):
                alerts["allergy_alerts"].append({
                    "allergen": "penicillin",
                    "proposed_drug": med.get("drug", ""),
                    "cross_reactivity": True,
                    "severity": "moderate",
                    "recommendation": f"Caution: ~2% cross-reactivity between penicillin and cephalosporins"
                })
        
        # Duplicate medication check
        for current_med in current_meds:
            if drug in current_med or current_med in drug:
                alerts["allergy_alerts"].append({
                    "allergen": "duplicate",
                    "proposed_drug": med.get("drug", ""),
                    "cross_reactivity": False,
                    "severity": "moderate",
                    "recommendation": f"Potential duplicate: patient already taking {current_med}"
                })
    
    return alerts


def _build_guardian_prompt(
    patient: dict[str, Any],
    proposed_orders: dict[str, Any],
    system_context: dict[str, Any] | None,
) -> str:
    """Build Guardian prompt."""
    parts = []
    
    parts.append(f"PATIENT: Age {patient.get('age', 'unknown')}, Gender {patient.get('gender', 'unknown')}")
    parts.append(f"WEIGHT: {patient.get('weight', 'unknown')} kg")
    
    allergies = patient.get("allergies", [])
    parts.append(f"ALLERGIES: {', '.join(allergies) if allergies else 'NKDA'}")
    
    medications = patient.get("medications", [])
    parts.append(f"CURRENT MEDICATIONS: {', '.join(medications) if medications else 'None'}")
    
    history = patient.get("history", [])
    parts.append(f"MEDICAL HISTORY: {', '.join(history) if history else 'None reported'}")
    
    parts.append(f"\nPROPOSED ORDERS:\n{json.dumps(proposed_orders, indent=2)}")
    
    if system_context:
        formulary = system_context.get("formulary_restrictions", [])
        if formulary:
            parts.append(f"FORMULARY RESTRICTIONS: {', '.join(formulary)}")
        protocols = system_context.get("protocols", [])
        if protocols:
            parts.append(f"HOSPITAL PROTOCOLS: {', '.join(protocols)}")
    
    return "\n".join(parts)


def _validate_guardian_output(result: dict) -> dict:
    """Validate Guardian output."""
    missing = []
    issues = []
    safety_flags = []
    
    if "overall_safety" not in result:
        missing.append("overall_safety")
    if "order_validations" not in result:
        missing.append("order_validations")
    
    safety = result.get("overall_safety", "")
    if safety == "unsafe":
        safety_flags.append("CRITICAL: Orders flagged as UNSAFE — review required before proceeding")
    
    blocked_orders = [o for o in result.get("order_validations", []) if o.get("status") == "blocked"]
    if blocked_orders:
        for bo in blocked_orders:
            safety_flags.append(f"BLOCKED: {bo.get('order_description', 'Unknown order')}")
    
    return {
        "schema_valid": len(missing) == 0,
        "missing_fields": missing,
        "logic_issues": issues,
        "safety_flags": safety_flags,
    }


def _generate_test_cases() -> list[dict]:
    return [
        {
            "name": "Safe order set",
            "input": {"medications": [{"drug": "Acetaminophen", "dose": "500mg"}], "allergies": []},
            "expected_behavior": "All orders approved, overall_safety=safe"
        },
        {
            "name": "Edge case — penicillin allergy + amoxicillin order",
            "input": {"medications": [{"drug": "Amoxicillin"}], "allergies": ["penicillin"]},
            "expected_behavior": "BLOCKED with critical allergy alert, overall_safety=unsafe"
        },
        {
            "name": "Failure case — overdose detection",
            "input": {"medications": [{"drug": "Metformin", "dose": "5000mg"}]},
            "expected_behavior": "Dosage alert flagged, recommendation to reduce dose"
        },
    ]
