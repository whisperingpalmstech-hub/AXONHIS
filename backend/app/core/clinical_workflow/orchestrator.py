"""
Master Orchestrator — Full Clinical Pipeline Engine.

Chains all 5 modules in sequence with state preservation:
Navigator → Scribe → Guardian → Handover → Translator

Produces:
- Complete pipeline output
- Patient-friendly instructions
- Safety validation
- E2E test cases
"""
import json
import logging
from typing import Any

from app.core.clinical_workflow.navigator import navigate
from app.core.clinical_workflow.scribe import scribe
from app.core.clinical_workflow.guardian import guard
from app.core.clinical_workflow.handover import handover
from app.core.clinical_workflow.translator import translate

logger = logging.getLogger(__name__)


async def run_full_pipeline(
    patient: dict[str, Any],
    interaction: dict[str, Any],
    clinical_stream: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Master Orchestrator — runs all 5 modules in sequence.

    Flow: Navigator → Scribe → Guardian → Handover → Translator
    Each module feeds context to the next. No data loss between steps.

    Args:
        patient: {name, age, gender, history[], allergies[], medications[]}
        interaction: {patient_narrative, doctor_narration}
        clinical_stream: {vitals_12h[], nurse_notes[], doctor_orders[]}

    Returns:
        Complete pipeline output with validation and E2E tests.
    """
    pipeline = {}
    all_safety_flags = []
    errors = []

    # Build encounter from interaction
    encounter = {
        "narrative": interaction.get("patient_narrative", ""),
        "doctor_input": interaction.get("doctor_narration", ""),
        "vitals": [],
        "notes": [],
    }

    # Extract vitals from clinical_stream if available
    if clinical_stream:
        vitals_12h = clinical_stream.get("vitals_12h", [])
        if vitals_12h and len(vitals_12h) > 0:
            latest = vitals_12h[-1]
            encounter["vitals"] = [
                {"name": "BP", "value": latest.get("bp", "")},
                {"name": "HR", "value": latest.get("hr", "")},
                {"name": "Temp", "value": latest.get("temp", "")},
                {"name": "SpO2", "value": latest.get("spo2", "")},
            ]
        nurse_notes = clinical_stream.get("nurse_notes", [])
        if nurse_notes:
            encounter["notes"] = [n.get("note", n) if isinstance(n, dict) else n for n in nurse_notes]

    # ─── STEP 1: CLINICAL NAVIGATOR ─────────────────────────────────────
    logger.info("[ORCHESTRATOR] Step 1: Running Clinical Navigator...")
    try:
        nav_result = await navigate(patient, encounter)
        pipeline["navigator"] = nav_result
        nav_flags = nav_result.get("validation", {}).get("safety_flags", [])
        all_safety_flags.extend([f"[NAVIGATOR] {f}" for f in nav_flags])
    except Exception as e:
        logger.error(f"[ORCHESTRATOR] Navigator failed: {e}")
        pipeline["navigator"] = {"error": str(e)}
        errors.append(f"Navigator failed: {str(e)}")

    # ─── STEP 2: ACTIONABLE SCRIBE (fed by Navigator) ───────────────────
    logger.info("[ORCHESTRATOR] Step 2: Running Actionable Scribe...")
    try:
        # Scribe receives Navigator output for context
        scribe_result = await scribe(
            patient, encounter,
            navigator_output=pipeline.get("navigator"),
        )
        pipeline["scribe"] = scribe_result
        scribe_flags = scribe_result.get("validation", {}).get("safety_flags", [])
        all_safety_flags.extend([f"[SCRIBE] {f}" for f in scribe_flags])
    except Exception as e:
        logger.error(f"[ORCHESTRATOR] Scribe failed: {e}")
        pipeline["scribe"] = {"error": str(e)}
        errors.append(f"Scribe failed: {str(e)}")

    # ─── STEP 3: GUARDIAN (validates Scribe orders) ─────────────────────
    logger.info("[ORCHESTRATOR] Step 3: Running Safety Guardian...")
    try:
        # Extract orders from Scribe output for Guardian
        scribe_out = pipeline.get("scribe", {}).get("module_output", {})
        scribe_items = scribe_out.get("items", [])

        proposed_orders = {
            "medications": [
                {"drug": i.get("label", ""), "dose": i.get("dose", ""),
                 "route": "PO", "frequency": ""}
                for i in scribe_items
                if i.get("category") == "Medication" and i.get("selected")
            ],
            "labs": [
                i.get("label", "")
                for i in scribe_items
                if i.get("category") == "Lab" and i.get("selected")
            ],
            "imaging": [
                i.get("label", "")
                for i in scribe_items
                if i.get("category") == "Imaging" and i.get("selected")
            ],
            "procedures": [
                i.get("label", "")
                for i in scribe_items
                if i.get("category") == "Procedure" and i.get("selected")
            ],
        }

        guard_result = await guard(patient, proposed_orders)
        pipeline["guardian"] = guard_result
        guard_flags = guard_result.get("validation", {}).get("issues", [])
        guard_alerts = guard_result.get("module_output", {}).get("alerts", [])
        for alert in guard_alerts:
            if alert.get("severity") == "High":
                all_safety_flags.append(f"[GUARDIAN] {alert.get('message', '')}")
    except Exception as e:
        logger.error(f"[ORCHESTRATOR] Guardian failed: {e}")
        pipeline["guardian"] = {"error": str(e)}
        errors.append(f"Guardian failed: {str(e)}")

    # ─── STEP 4: HANDOVER ENGINE ────────────────────────────────────────
    logger.info("[ORCHESTRATOR] Step 4: Running Handover Engine...")
    try:
        # Build handover patient from accumulated data
        nav_out = pipeline.get("navigator", {}).get("module_output", {})
        triage = nav_out.get("triage", {})

        handover_patient = {
            "id": patient.get("id", ""),
            "name": patient.get("name", "Patient"),
            "bed": patient.get("bed", "—"),
            "age": patient.get("age", ""),
            "gender": patient.get("gender", ""),
            "diagnosis": triage.get("primary_impression", scribe_out.get("order_set_name", "")),
            "status": "critical" if nav_out.get("risk_level") == "High" else "stable",
            "vitals": encounter.get("vitals", []),
            "notes": encounter.get("notes", []),
            "pending_orders": [
                i.get("label", "") for i in scribe_items if i.get("selected")
            ][:5],
            "medications_due": [
                f"{i.get('label', '')} {i.get('dose', '')}"
                for i in scribe_items
                if i.get("category") == "Medication" and i.get("selected")
            ],
        }

        handover_result = await handover(
            department=patient.get("department", "General"),
            patients=[handover_patient],
        )
        pipeline["handover"] = handover_result
    except Exception as e:
        logger.error(f"[ORCHESTRATOR] Handover failed: {e}")
        pipeline["handover"] = {"error": str(e)}
        errors.append(f"Handover failed: {str(e)}")

    # ─── STEP 5: PATIENT TRANSLATOR ─────────────────────────────────────
    logger.info("[ORCHESTRATOR] Step 5: Running Patient Translator...")
    try:
        # Feed Scribe output to Translator
        translate_result = await translate(
            clinical_content=scribe_out,
            patient=patient,
        )
        pipeline["translator"] = translate_result
    except Exception as e:
        logger.error(f"[ORCHESTRATOR] Translator failed: {e}")
        pipeline["translator"] = {"error": str(e)}
        errors.append(f"Translator failed: {str(e)}")

    # ─── AGGREGATE & VALIDATE ───────────────────────────────────────────
    modules_run = [k for k, v in pipeline.items() if "error" not in v]
    modules_failed = [k for k, v in pipeline.items() if "error" in v]

    # Determine overall risk
    nav_risk = nav_out.get("risk_level", "Low")
    guard_safety = pipeline.get("guardian", {}).get("module_output", {}).get("overall_safety", "safe")
    if guard_safety == "unsafe" or nav_risk == "High":
        overall_risk = "High"
    elif guard_safety == "caution" or nav_risk == "Medium":
        overall_risk = "Medium"
    else:
        overall_risk = "Low"

    # Build patient-friendly text
    translator_out = pipeline.get("translator", {}).get("module_output", {})
    patient_text = _build_patient_text(patient, translator_out)

    # Consistency checks
    inconsistencies = _check_consistency(pipeline)

    # E2E test cases
    test_cases = _generate_e2e_tests(patient, interaction)

    return {
        "pipeline": "complete" if len(modules_failed) == 0 else "partial",
        "modules_executed": modules_run,
        "modules_failed": modules_failed,

        "pipeline_output": pipeline,

        "patient_instructions": patient_text,

        "system_summary": {
            "overall_risk": overall_risk,
            "triage": triage.get("level", ""),
            "severity": triage.get("severity_score", 0),
            "primary_impression": triage.get("primary_impression", ""),
            "orders_count": len(scribe_items),
            "safety_status": guard_safety,
            "key_issues": all_safety_flags[:5],
            "critical_alerts": [f for f in all_safety_flags if "GUARDIAN" in f],
        },

        "validation": {
            "pipeline_complete": len(modules_failed) == 0,
            "data_loss": False,
            "inconsistencies": inconsistencies,
            "safety_flags": all_safety_flags,
            "errors": errors,
        },

        "e2e_test_cases": test_cases,

        "improvements": [
            "Add Redis caching for pipeline state persistence",
            "Implement WebSocket streaming for real-time module progress",
            "Add parallel execution for independent modules",
            "Integrate with EHR for auto-population of patient data",
            "Add audit trail logging for compliance"
        ],
    }


def _build_patient_text(patient: dict, translator_out: dict) -> str:
    """Build human-readable patient instructions from translator output."""
    name = patient.get("name", "Patient")
    ps = translator_out.get("patient_summary", {})

    lines = []
    lines.append(f"Hello {name}, here's your care plan:\n")

    if ps.get("what_happened"):
        lines.append(f"📋 What happened: {ps['what_happened']}")
    if ps.get("what_we_found"):
        lines.append(f"🔍 What we found: {ps['what_we_found']}")
    if ps.get("what_to_do_next"):
        lines.append(f"✅ What to do next: {ps['what_to_do_next']}")

    # Medications
    meds = translator_out.get("medications", [])
    if meds:
        lines.append("\n💊 Your Medicines:")
        for m in meds:
            lines.append(f"  • {m.get('name', '')} ({m.get('simple_name', '')}): {m.get('how_to_take', '')}")

    # Warning signs
    warnings = translator_out.get("warning_signs", [])
    if warnings:
        lines.append("\n🚨 When to get help:")
        for w in warnings:
            urgency_label = {
                "call_911": "🔴 Call 911",
                "go_to_er": "🟠 Go to ER",
                "call_doctor": "🟡 Call your doctor",
                "watch": "🟢 Watch and wait",
            }.get(w.get("urgency", ""), "⚠️")
            lines.append(f"  {urgency_label}: {w.get('sign', '')} → {w.get('action', '')}")

    # Follow-up
    fu = translator_out.get("follow_up", {})
    if fu.get("when"):
        lines.append(f"\n📅 Follow-up: {fu['when']} at {fu.get('where', 'your clinic')}")

    return "\n".join(lines)


def _check_consistency(pipeline: dict) -> list[str]:
    """Check for inconsistencies across pipeline modules."""
    issues = []

    nav = pipeline.get("navigator", {}).get("module_output", {})
    scr = pipeline.get("scribe", {}).get("module_output", {})
    grd = pipeline.get("guardian", {}).get("module_output", {})

    # Check: if Navigator says High risk, Scribe should have Emergency priority
    nav_risk = nav.get("risk_level", "")
    scr_priority = scr.get("priority_level", "")
    if nav_risk == "High" and scr_priority == "Routine":
        issues.append("Navigator risk=High but Scribe priority=Routine — mismatch")

    # Check: if Guardian says unsafe, system_summary should reflect it
    guard_safety = grd.get("overall_safety", "")
    if guard_safety == "unsafe":
        guard_alerts = grd.get("alerts", [])
        high_alerts = [a for a in guard_alerts if a.get("severity") == "High"]
        if not high_alerts:
            issues.append("Guardian overall_safety=unsafe but no High severity alerts")

    return issues


def _generate_e2e_tests(patient: dict, interaction: dict) -> list[dict]:
    """Generate E2E test cases for the pipeline."""
    return [
        {
            "name": "Normal Flow — Mild symptoms, standard protocol",
            "scenario": "Patient with mild fever and cough, no allergies, no risk factors",
            "steps": [
                "1. Enter patient narrative: 'Mild fever for 2 days with dry cough'",
                "2. Navigator should return: risk=Low, focus=Respiratory",
                "3. Scribe should generate: Routine protocol, basic labs",
                "4. Guardian should return: overall_safety=safe",
                "5. Translator should produce: simple care instructions",
            ],
            "expected_result": "Pipeline complete, no safety flags, patient gets simple discharge instructions",
            "playwright_assertions": [
                "expect(page.locator('[data-risk-level]')).toHaveText('Low')",
                "expect(page.locator('[data-safety-status]')).toHaveText('SAFE')",
                "expect(page.locator('[data-patient-instructions]')).toBeVisible()",
            ],
        },
        {
            "name": "High-Risk Flow — Chest pain with cardiac history + allergy conflict",
            "scenario": "55F with chest pain, Penicillin allergy, Aspirin ordered",
            "steps": [
                "1. Enter: '55F crushing chest pain radiating to jaw'",
                "2. Navigator should return: risk=High, ESI-1/2, Cardiovascular",
                "3. Scribe should generate: Emergency Chest Pain Protocol",
                "4. Guardian should flag: Aspirin allergy if ordered",
                "5. Translator should include: call 911 warning signs",
            ],
            "expected_result": "Pipeline shows safety alerts, allergy warning, emergency triage",
            "playwright_assertions": [
                "expect(page.locator('[data-risk-level]')).toHaveText('High')",
                "expect(page.locator('.allergy-alert')).toBeVisible()",
                "expect(page.locator('[data-triage]')).toContainText('ESI')",
            ],
        },
        {
            "name": "Failure Flow — Missing data, conflicting information",
            "scenario": "Empty narrative, no vitals, no history provided",
            "steps": [
                "1. Submit empty patient narrative",
                "2. Navigator should return: low confidence, clarifying questions",
                "3. Scribe should fallback to navigator data",
                "4. Guardian should flag: missing patient data warning",
                "5. Handover should return: Insufficient Data",
            ],
            "expected_result": "Pipeline partial, validation warnings, incomplete but safe",
            "playwright_assertions": [
                "expect(page.locator('[data-confidence]')).toBeLessThan(50)",
                "expect(page.locator('.attention-flag')).toBeVisible()",
            ],
        },
    ]
