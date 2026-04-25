"""
Module 4: Handover Engine — Shift Summary Generator.

Auto-generates SBAR-format shift handover summaries from patient encounter data.
"""
import json
import logging
from typing import Any

from app.core.ai.grok_client import grok_json

logger = logging.getLogger(__name__)


HANDOVER_SYSTEM_PROMPT = """You are a Clinical Handover AI — an expert shift summary and continuity-of-care system.

Given a list of patients with their encounters, orders, and status, generate an SBAR-format handover report.

Return a JSON object with this EXACT structure:

{
  "handover_summary": {
    "shift": "",
    "department": "",
    "generated_at": "",
    "total_patients": 0,
    "critical_patients": 0,
    "new_admissions": 0,
    "pending_discharges": 0
  },
  "patient_handovers": [
    {
      "patient_id": "",
      "patient_name": "",
      "bed": "",
      "situation": "",
      "background": "",
      "assessment": "",
      "recommendation": "",
      "acuity": "critical|high|moderate|stable",
      "pending_actions": [],
      "critical_values": [],
      "escalation_needed": false,
      "escalation_reason": ""
    }
  ],
  "department_alerts": [],
  "pending_results": [],
  "medication_due": [],
  "follow_up_items": []
}

RULES:
- Use SBAR format strictly
- Prioritize critical patients first
- Flag all pending actions clearly
- Include ALL pending lab results
- Highlight medication timing
- Return valid JSON ONLY
"""


async def handover(
    department: str,
    patients: list[dict[str, Any]],
    shift_info: dict[str, Any] | None = None,
    system_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Generate shift handover summary.
    
    Args:
        department: Ward/department name
        patients: List of patient data with encounters and orders
        shift_info: Current shift details (outgoing/incoming)
        system_context: Hospital handover protocols
    
    Returns:
        SBAR-format handover report.
    """
    user_message = _build_handover_prompt(department, patients, shift_info)
    
    messages = [
        {"role": "system", "content": HANDOVER_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    
    try:
        result = await grok_json(messages, temperature=0.2, max_tokens=2500)
        validation = _validate_handover_output(result, patients)
        
        return {
            "module": "handover_engine",
            "module_output": result,
            "validation": validation,
            "test_cases": _generate_test_cases(),
            "improvements": [
                "Add real-time vitals trend integration",
                "Include medication administration record (MAR) summary",
                "Add automated escalation to on-call physician",
                "Support multi-language handover for international staff"
            ],
            "next_step": "patient_translator"
        }
    except Exception as e:
        logger.error(f"Handover Engine error: {e}")
        return {
            "module": "handover_engine",
            "module_output": {},
            "validation": {
                "schema_valid": False,
                "missing_fields": [],
                "logic_issues": [f"AI processing failed: {str(e)}"],
                "safety_flags": ["Handover AI unavailable — manual handover required"]
            },
            "test_cases": [],
            "improvements": [],
            "next_step": "manual_handover"
        }


def _build_handover_prompt(
    department: str,
    patients: list[dict[str, Any]],
    shift_info: dict[str, Any] | None,
) -> str:
    """Build Handover prompt."""
    parts = [f"DEPARTMENT: {department}"]
    
    if shift_info:
        parts.append(f"SHIFT: {shift_info.get('shift_type', 'unknown')} ({shift_info.get('start', '')} - {shift_info.get('end', '')})")
        parts.append(f"OUTGOING STAFF: {shift_info.get('outgoing_staff', 'N/A')}")
        parts.append(f"INCOMING STAFF: {shift_info.get('incoming_staff', 'N/A')}")
    
    parts.append(f"\nTOTAL PATIENTS: {len(patients)}\n")
    
    for i, pt in enumerate(patients, 1):
        parts.append(f"--- PATIENT {i} ---")
        parts.append(f"Name: {pt.get('name', 'Unknown')}")
        parts.append(f"ID: {pt.get('id', 'N/A')}")
        parts.append(f"Bed: {pt.get('bed', 'N/A')}")
        parts.append(f"Age/Gender: {pt.get('age', '?')}/{pt.get('gender', '?')}")
        parts.append(f"Admission Diagnosis: {pt.get('diagnosis', 'N/A')}")
        parts.append(f"Current Status: {pt.get('status', 'stable')}")
        
        vitals = pt.get("vitals", [])
        if vitals:
            vitals_str = ", ".join([f"{v.get('name')}: {v.get('value')}" for v in vitals])
            parts.append(f"Latest Vitals: {vitals_str}")
        
        orders = pt.get("pending_orders", [])
        if orders:
            parts.append(f"Pending Orders: {', '.join(orders)}")
        
        meds = pt.get("medications_due", [])
        if meds:
            parts.append(f"Medications Due: {', '.join(meds)}")
        
        notes = pt.get("notes", [])
        if notes:
            parts.append(f"Notes: {'; '.join(notes)}")
        
        parts.append("")
    
    return "\n".join(parts)


def _validate_handover_output(result: dict, patients: list) -> dict:
    """Validate Handover output."""
    missing = []
    issues = []
    safety_flags = []
    
    if "handover_summary" not in result:
        missing.append("handover_summary")
    if "patient_handovers" not in result:
        missing.append("patient_handovers")
    
    # Check all patients are covered
    handovers = result.get("patient_handovers", [])
    if len(handovers) < len(patients):
        issues.append(f"Only {len(handovers)}/{len(patients)} patients covered in handover")
    
    # Check for escalation needs
    for ho in handovers:
        if ho.get("escalation_needed"):
            safety_flags.append(f"ESCALATION NEEDED: {ho.get('patient_name', 'Unknown')} — {ho.get('escalation_reason', '')}")
        if ho.get("acuity") == "critical":
            safety_flags.append(f"CRITICAL PATIENT: {ho.get('patient_name', 'Unknown')} — immediate attention required")
    
    return {
        "schema_valid": len(missing) == 0,
        "missing_fields": missing,
        "logic_issues": issues,
        "safety_flags": safety_flags,
    }


def _generate_test_cases() -> list[dict]:
    return [
        {
            "name": "Normal ward handover",
            "input": {"department": "General Ward", "patients": [{"name": "John", "status": "stable"}]},
            "expected_behavior": "Complete SBAR for each patient, no escalations"
        },
        {
            "name": "Edge case — ICU with critical patient",
            "input": {"department": "ICU", "patients": [{"name": "Jane", "status": "critical", "vitals": [{"name": "BP", "value": "80/50"}]}]},
            "expected_behavior": "Critical acuity flag, escalation_needed=true"
        },
        {
            "name": "Failure case — empty patient list",
            "input": {"department": "ER", "patients": []},
            "expected_behavior": "Valid empty handover with 0 patients summary"
        },
    ]
