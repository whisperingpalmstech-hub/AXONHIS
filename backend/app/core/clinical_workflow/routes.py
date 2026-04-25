"""
Clinical Workflow Engine — Unified API Router.

Exposes all 5 clinical workflow modules as REST endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Optional

from app.core.clinical_workflow.navigator import navigate
from app.core.clinical_workflow.scribe import scribe
from app.core.clinical_workflow.guardian import guard
from app.core.clinical_workflow.handover import handover
from app.core.clinical_workflow.translator import translate

router = APIRouter(prefix="/api/v1/clinical-workflow", tags=["Clinical Workflow Engine"])


# ── Pydantic Models ──────────────────────────────────────────────────────

class PatientInput(BaseModel):
    id: str = ""
    age: str | int = ""
    gender: str = ""
    name: str = ""
    weight: str | float = ""
    history: list[str] = []
    allergies: list[str] = []
    medications: list[str] = []


class EncounterInput(BaseModel):
    narrative: str = ""
    doctor_input: str = ""
    vitals: list[dict[str, Any]] = []
    notes: list[str] = []


class SystemContext(BaseModel):
    protocols: list[str] = []
    hospital_rules: list[str] = []
    formulary_restrictions: list[str] = []


class NavigateRequest(BaseModel):
    patient: PatientInput
    encounter: EncounterInput
    system_context: Optional[SystemContext] = None


class ScribeRequest(BaseModel):
    patient: PatientInput
    encounter: EncounterInput
    navigator_output: Optional[dict[str, Any]] = None
    system_context: Optional[SystemContext] = None


class GuardRequest(BaseModel):
    patient: PatientInput
    proposed_orders: dict[str, Any] = {}
    system_context: Optional[SystemContext] = None


class ShiftInfo(BaseModel):
    shift_type: str = "day"
    start: str = ""
    end: str = ""
    outgoing_staff: str = ""
    incoming_staff: str = ""


class HandoverPatient(BaseModel):
    id: str = ""
    name: str = ""
    bed: str = ""
    age: str | int = ""
    gender: str = ""
    diagnosis: str = ""
    status: str = "stable"
    vitals: list[dict[str, Any]] = []
    pending_orders: list[str] = []
    medications_due: list[str] = []
    notes: list[str] = []


class HandoverRequest(BaseModel):
    department: str
    patients: list[HandoverPatient] = []
    shift_info: Optional[ShiftInfo] = None
    system_context: Optional[SystemContext] = None


class TranslateRequest(BaseModel):
    clinical_content: dict[str, Any]
    patient: Optional[PatientInput] = None
    target_language: str = "en"
    reading_level: str = "grade_5"


class FullPipelineRequest(BaseModel):
    """Run the entire clinical workflow pipeline end-to-end."""
    patient: PatientInput
    encounter: EncounterInput
    system_context: Optional[SystemContext] = None


# ── Endpoints ────────────────────────────────────────────────────────────

@router.post("/navigate")
async def api_navigate(req: NavigateRequest):
    """Module 1: Clinical Navigator — Intake Intelligence."""
    result = await navigate(
        patient=req.patient.model_dump(),
        encounter=req.encounter.model_dump(),
        system_context=req.system_context.model_dump() if req.system_context else None,
    )
    return result


@router.post("/scribe")
async def api_scribe(req: ScribeRequest):
    """Module 2: Actionable Scribe — SOAP + Orders."""
    result = await scribe(
        patient=req.patient.model_dump(),
        encounter=req.encounter.model_dump(),
        navigator_output=req.navigator_output,
        system_context=req.system_context.model_dump() if req.system_context else None,
    )
    return result


@router.post("/guard")
async def api_guard(req: GuardRequest):
    """Module 3: Guardian — Safety & Compliance."""
    result = await guard(
        patient=req.patient.model_dump(),
        proposed_orders=req.proposed_orders,
        system_context=req.system_context.model_dump() if req.system_context else None,
    )
    return result


@router.post("/handover")
async def api_handover(req: HandoverRequest):
    """Module 4: Handover Engine — Shift Summary."""
    result = await handover(
        department=req.department,
        patients=[p.model_dump() for p in req.patients],
        shift_info=req.shift_info.model_dump() if req.shift_info else None,
        system_context=req.system_context.model_dump() if req.system_context else None,
    )
    return result


@router.post("/translate")
async def api_translate(req: TranslateRequest):
    """Module 5: Patient Translator — Human-Friendly Output."""
    result = await translate(
        clinical_content=req.clinical_content,
        patient=req.patient.model_dump() if req.patient else None,
        target_language=req.target_language,
        reading_level=req.reading_level,
    )
    return result


@router.post("/pipeline")
async def api_full_pipeline(req: FullPipelineRequest):
    """
    Full Pipeline: Navigator → Scribe → Guardian → Translator.
    
    Runs all modules sequentially, passing context between them.
    """
    patient = req.patient.model_dump()
    encounter = req.encounter.model_dump()
    system_ctx = req.system_context.model_dump() if req.system_context else None
    
    pipeline_results = {}
    
    # Step 1: Navigate
    nav_result = await navigate(patient, encounter, system_ctx)
    pipeline_results["navigator"] = nav_result
    
    # Step 2: Scribe (uses navigator output)
    scribe_result = await scribe(patient, encounter, nav_result, system_ctx)
    pipeline_results["scribe"] = scribe_result
    
    # Step 3: Guard (validates scribe's orders)
    scribe_orders = scribe_result.get("module_output", {}).get("suggested_orders", {})
    guard_result = await guard(patient, scribe_orders, system_ctx)
    pipeline_results["guardian"] = guard_result
    
    # Step 4: Translate (patient-friendly output)
    translate_result = await translate(
        clinical_content=scribe_result.get("module_output", {}),
        patient=patient,
    )
    pipeline_results["translator"] = translate_result
    
    # Aggregate safety flags
    all_safety_flags = []
    for module_name, module_result in pipeline_results.items():
        flags = module_result.get("validation", {}).get("safety_flags", [])
        for flag in flags:
            all_safety_flags.append(f"[{module_name.upper()}] {flag}")
    
    return {
        "pipeline": "complete",
        "modules_executed": list(pipeline_results.keys()),
        "results": pipeline_results,
        "aggregate_safety_flags": all_safety_flags,
        "overall_status": "unsafe" if any("CRITICAL" in f for f in all_safety_flags) else "safe",
    }


@router.get("/status")
async def api_status():
    """Check Clinical Workflow Engine status."""
    return {
        "engine": "Clinical Workflow Engine",
        "version": "1.0.0",
        "modules": [
            {"name": "Clinical Navigator", "status": "active", "endpoint": "/navigate"},
            {"name": "Actionable Scribe", "status": "active", "endpoint": "/scribe"},
            {"name": "Guardian", "status": "active", "endpoint": "/guard"},
            {"name": "Handover Engine", "status": "active", "endpoint": "/handover"},
            {"name": "Patient Translator", "status": "active", "endpoint": "/translate"},
            {"name": "Full Pipeline", "status": "active", "endpoint": "/pipeline"},
        ],
        "ai_provider": "AnythingLLM",
        "status": "operational"
    }
