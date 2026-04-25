"""
Module 4: Handover Engine — Shift Summary Intelligence.

Converts last 12h of patient data into high-density clinical briefings:
1. Vital trend analysis (improvement/decline/stability)
2. Event extraction (new symptoms, deterioration, interventions)
3. Change detection (only what changed, not stable info)
4. Task extraction (pending, time-sensitive, follow-ups)
5. Status classification (Stable/Guarded/Deteriorating)
6. Prioritization (life-threatening first)

Acts like a senior charge nurse summarizing a patient in 30 seconds.
"""
import json
import logging
from typing import Any

from app.core.ai.grok_client import grok_json

logger = logging.getLogger(__name__)


HANDOVER_SYSTEM_PROMPT = """You are the Handover Engine — a senior charge nurse AI that creates ultra-concise shift summaries.

Your role: Convert 12 hours of patient data into a 30-second briefing for incoming staff.

CRITICAL RULE: Include ONLY what changed. DO NOT repeat stable, unchanged information.

PROCESSING LOGIC (follow ALL 6 steps for EACH patient):

STEP 1: VITAL TREND ANALYSIS
Compare earliest vs latest vitals. Detect: improvement, decline, stability, sudden spikes/drops.

STEP 2: EVENT EXTRACTION
From nurse notes + doctor orders, identify: new symptoms, clinical deterioration, interventions performed, escalations (ICU, oxygen, blood products).

STEP 3: CHANGE DETECTION (CRITICAL)
ONLY include what changed, worsened, or improved. IGNORE stable values and repeated info.

STEP 4: TASK EXTRACTION
From pending doctor orders: time-sensitive actions, follow-ups required, incomplete tasks.

STEP 5: STATUS CLASSIFICATION
- Stable → No significant change in 12h
- Guarded → Some concern, fluctuating vitals, or new minor symptoms
- Deteriorating → Clear worsening trend, escalation needed

STEP 6: PRIORITIZATION
Rank items: 1) Life-threatening changes, 2) New symptoms, 3) Pending critical tasks, 4) Minor updates.

For EACH patient, return a JSON object in this structure. When multiple patients are given, return an array.

Single patient output:
{
  "patient_id": "",
  "patient_name": "",
  "bed": "",
  "status_summary": "Stable|Guarded|Deteriorating|Insufficient Data",
  "status_color": "green|amber|red|gray",

  "one_liner": "Single sentence summary of the patient's current state and key change",

  "critical_changes": [
    "Only significant changes in last 12h (max 5)"
  ],

  "pending_tasks": [
    "Actionable tasks for incoming staff (max 5)"
  ],

  "vitals_trend": {
    "direction": "Improving|Declining|Stable|Mixed",
    "details": "Brief trend description",
    "latest_vitals": {"bp": "", "hr": "", "temp": "", "spo2": "", "rr": ""}
  },

  "attention_flags": [
    "Missing data warnings, inconsistencies, or safety concerns"
  ],

  "handover_priority": 1
}

For multiple patients, wrap in:
{
  "department": "",
  "shift_summary": "Brief department-level overview",
  "total_patients": 0,
  "critical_count": 0,
  "patients": [ ... array of patient objects ... ]
}

HARD CONSTRAINTS:
- DO NOT include unchanged/stable data in critical_changes
- DO NOT exceed 5 bullets per section
- DO NOT output unstructured text
- DO NOT miss critical deterioration
- Patients with Deteriorating status MUST have handover_priority=1
- Return valid JSON ONLY
"""


async def handover(
    department: str,
    patients: list[dict[str, Any]],
    shift_info: dict[str, Any] | None = None,
    system_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Run Handover Engine for shift summary generation.

    Args:
        department: Ward/department name
        patients: List of patient data with vitals_12h, nurse_notes, doctor_orders
        shift_info: Shift metadata (type, staff, times)
        system_context: Hospital protocols

    Returns:
        Prioritized shift handover briefing.
    """
    user_message = _build_handover_prompt(department, patients, shift_info, system_context)

    messages = [
        {"role": "system", "content": HANDOVER_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        result = await grok_json(messages, temperature=0.2, max_tokens=3000)
        validation = _validate_handover_output(result, patients)

        return {
            "module": "handover_engine",
            "module_output": result,
            "validation": validation,
            "test_cases": _generate_test_cases(),
            "improvements": [
                "Add urine output and GCS tracking for ICU patients",
                "Implement NEWS2 early warning score trending",
                "Better alert prioritization based on clinical severity scores",
                "Add medication administration timeline gaps detection",
                "Track fluid balance and I/O charting"
            ],
            "next_step": "translator"
        }
    except Exception as e:
        logger.error(f"Handover Engine error: {e}")
        return {
            "module": "handover_engine",
            "module_output": {
                "department": department,
                "shift_summary": f"Handover generation failed: {str(e)}",
                "patients": [],
            },
            "validation": {"schema_valid": False, "issues": [str(e)]},
            "test_cases": [],
            "improvements": [],
            "next_step": "manual_handover"
        }


def _build_handover_prompt(
    department: str,
    patients: list[dict[str, Any]],
    shift_info: dict[str, Any] | None,
    system_context: dict[str, Any] | None,
) -> str:
    """Build the user prompt for the Handover Engine."""
    parts = []

    parts.append(f"DEPARTMENT: {department}")

    # Shift info
    if shift_info:
        parts.append(f"SHIFT: {shift_info.get('shift_type', 'day')} shift")
        parts.append(f"  Outgoing: {shift_info.get('outgoing_staff', 'N/A')}")
        parts.append(f"  Incoming: {shift_info.get('incoming_staff', 'N/A')}")
        parts.append(f"  Period: {shift_info.get('start', '')} → {shift_info.get('end', '')}")

    parts.append(f"\nPATIENTS ({len(patients)}):")
    parts.append("=" * 50)

    for i, pt in enumerate(patients, 1):
        parts.append(f"\n--- Patient {i}: {pt.get('name', 'Unknown')} ---")
        parts.append(f"  ID: {pt.get('id', 'N/A')}")
        parts.append(f"  Bed: {pt.get('bed', 'N/A')}")
        parts.append(f"  Age: {pt.get('age', '?')}, Gender: {pt.get('gender', '?')}")
        parts.append(f"  Diagnosis: {pt.get('diagnosis', 'N/A')}")
        parts.append(f"  Current status: {pt.get('status', 'unknown')}")

        # Vitals over 12h
        vitals_12h = pt.get("vitals_12h", pt.get("vitals", []))
        if vitals_12h:
            parts.append("  VITALS (12h):")
            for v in vitals_12h:
                if isinstance(v, dict):
                    ts = v.get("timestamp", "")
                    bp = v.get("bp", f"{v.get('name', '')}: {v.get('value', '')}")
                    parts.append(f"    [{ts}] BP:{v.get('bp','-')} HR:{v.get('hr','-')} Temp:{v.get('temp','-')} SpO2:{v.get('spo2','-')}")
        else:
            parts.append("  VITALS: (no vitals recorded — FLAG)")

        # Nurse notes
        notes = pt.get("nurse_notes", pt.get("notes", []))
        if notes:
            parts.append("  NURSE NOTES:")
            for n in notes:
                if isinstance(n, dict):
                    parts.append(f"    [{n.get('timestamp', '')}] {n.get('note', '')}")
                else:
                    parts.append(f"    - {n}")

        # Doctor orders
        orders = pt.get("doctor_orders", pt.get("pending_orders", []))
        if orders:
            parts.append("  DOCTOR ORDERS:")
            for o in orders:
                if isinstance(o, dict):
                    parts.append(f"    [{o.get('timestamp', '')}] {o.get('order', '')} — {o.get('status', 'pending')}")
                else:
                    parts.append(f"    - {o} (pending)")

        # Medications due
        meds_due = pt.get("medications_due", [])
        if meds_due:
            parts.append(f"  MEDICATIONS DUE: {', '.join(meds_due)}")

    return "\n".join(parts)


def _validate_handover_output(result: dict, patients: list) -> dict:
    """Validate Handover output."""
    issues = []

    # Check structure
    if isinstance(result, dict) and "patients" in result:
        patient_summaries = result["patients"]
    elif isinstance(result, list):
        patient_summaries = result
    else:
        # Single patient result
        patient_summaries = [result]

    for ps in patient_summaries:
        if not ps.get("status_summary"):
            issues.append(f"Missing status_summary for {ps.get('patient_name', 'unknown')}")
        if not ps.get("one_liner"):
            issues.append(f"Missing one_liner for {ps.get('patient_name', 'unknown')}")

        # Critical: deteriorating patients must have high priority
        if ps.get("status_summary") == "Deteriorating" and ps.get("handover_priority", 99) > 1:
            issues.append(f"Deteriorating patient {ps.get('patient_name')} should have priority 1")

        # Max 5 items per section
        for field in ["critical_changes", "pending_tasks", "attention_flags"]:
            items = ps.get(field, [])
            if len(items) > 5:
                issues.append(f"Too many items in {field} ({len(items)} > 5)")

    return {
        "schema_valid": len(issues) == 0,
        "issues": issues,
        "patients_summarized": len(patient_summaries),
    }


def _generate_test_cases() -> list[dict]:
    return [
        {
            "name": "Stable case — no changes in 12h",
            "input": {
                "vitals_12h": [
                    {"timestamp": "06:00", "bp": "120/80", "hr": "72", "temp": "36.8", "spo2": "98"},
                    {"timestamp": "12:00", "bp": "118/78", "hr": "70", "temp": "36.7", "spo2": "99"},
                ],
                "nurse_notes": [{"timestamp": "10:00", "note": "Patient resting comfortably, no complaints."}],
                "doctor_orders": []
            },
            "expected_behavior": "status_summary=Stable, vitals_trend=Stable, minimal critical_changes, short one_liner"
        },
        {
            "name": "Deteriorating case — vitals worsening",
            "input": {
                "vitals_12h": [
                    {"timestamp": "06:00", "bp": "130/85", "hr": "80", "temp": "37.0", "spo2": "96"},
                    {"timestamp": "12:00", "bp": "90/60", "hr": "110", "temp": "38.9", "spo2": "88"},
                ],
                "nurse_notes": [{"timestamp": "11:00", "note": "Patient febrile, tachycardic, desatting."}],
                "doctor_orders": [{"order": "Blood cultures", "status": "pending"}, {"order": "IV fluids stat", "status": "completed"}]
            },
            "expected_behavior": "status_summary=Deteriorating, vitals_trend=Declining, critical_changes highlighted, handover_priority=1"
        },
        {
            "name": "Mixed signals — conflicting data",
            "input": {
                "vitals_12h": [
                    {"timestamp": "06:00", "bp": "140/90", "hr": "90", "temp": "38.0", "spo2": "94"},
                    {"timestamp": "12:00", "bp": "125/80", "hr": "85", "temp": "37.2", "spo2": "97"},
                ],
                "nurse_notes": [{"timestamp": "10:00", "note": "Patient improving"}, {"timestamp": "11:30", "note": "New onset confusion noted"}],
                "doctor_orders": []
            },
            "expected_behavior": "status_summary=Guarded, vitals_trend=Improving but attention_flags for confusion"
        },
    ]
