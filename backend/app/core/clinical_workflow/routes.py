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
from app.core.clinical_workflow.orchestrator import run_full_pipeline

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
    Master Orchestrator Pipeline: Navigator → Scribe → Guardian → Handover → Translator.
    
    Runs all 5 modules sequentially with state preservation.
    """
    patient = req.patient.model_dump()
    interaction = {
        "patient_narrative": req.encounter.narrative,
        "doctor_narration": req.encounter.doctor_input,
    }
    
    return await run_full_pipeline(patient, interaction)


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


# ── Doctor Desk Integration: Patient-Context-Aware Endpoints ─────────────

class DeskAIRequest(BaseModel):
    """Request from Doctor Desk — auto-fetches patient context from DB."""
    patient_id: str
    visit_id: str = ""
    doctor_input: str = ""
    module: str = "navigate"  # navigate | scribe | guard | pipeline
    # Optional overrides (if doctor desk already has data loaded)
    vitals_override: list[dict[str, Any]] = []
    complaints_override: list[str] = []
    history_override: list[str] = []
    allergies_override: list[str] = []
    medications_override: list[str] = []


@router.post("/desk/ai")
async def api_desk_ai(req: DeskAIRequest):
    """
    Doctor Desk Integration — run AI modules with real patient context.
    
    The frontend passes patient_id + doctor_input + any loaded EMR data.
    This endpoint assembles the full context and runs the requested module.
    """
    # Build patient context from overrides (already loaded in frontend)
    patient = {
        "id": req.patient_id,
        "age": "",
        "gender": "",
        "history": req.history_override,
        "allergies": req.allergies_override,
        "medications": req.medications_override,
    }
    
    encounter = {
        "narrative": req.doctor_input,
        "doctor_input": req.doctor_input,
        "vitals": req.vitals_override,
        "notes": req.complaints_override,
    }
    
    if req.module == "navigate":
        return await navigate(patient, encounter)
    
    elif req.module == "scribe":
        return await scribe(patient, encounter)
    
    elif req.module == "guard":
        # For guard, we first run scribe to get orders, then validate
        scribe_result = await scribe(patient, encounter)
        scribe_items = scribe_result.get("module_output", {}).get("items", [])
        medications = [
            {"drug": i.get("label", ""), "dose": i.get("dose", "")}
            for i in scribe_items if i.get("category") == "Medication" and i.get("selected")
        ]
        guard_result = await guard(patient, {"medications": medications})
        return {
            "scribe": scribe_result,
            "guardian": guard_result,
        }
    
    elif req.module == "pipeline":
        # Master Orchestrator: all 5 modules with state preservation
        interaction = {
            "patient_narrative": req.doctor_input,
            "doctor_narration": req.doctor_input,
        }
        clinical_stream = {
            "vitals_12h": req.vitals_override,
        }
        return await run_full_pipeline(patient, interaction, clinical_stream)
    
    else:
        raise HTTPException(400, f"Unknown module: {req.module}")

