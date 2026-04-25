"""
Patient Portal — Clinical Workflow Integration.

Exposes patient-friendly translated content via the portal API.
Patients can view their AI-translated discharge instructions,
medication guides, and care plans.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
import uuid

from app.core.clinical_workflow.translator import translate

router = APIRouter(prefix="/health-summary", tags=["Patient Portal - Health Summary"])


class PatientTranslateRequest(BaseModel):
    clinical_note: str = ""
    discharge_summary: str = ""
    patient_name: str = ""
    patient_age: str = ""
    language: str = "en"
    reading_level: str = "grade_5"


@router.post("/translate")
async def portal_translate(req: PatientTranslateRequest):
    """
    Generate patient-friendly health summary from clinical content.
    Used by the Patient Portal to show understandable discharge instructions.
    """
    clinical_content = {}
    if req.clinical_note:
        clinical_content["clinical_note"] = req.clinical_note
    if req.discharge_summary:
        clinical_content["discharge_summary"] = req.discharge_summary

    if not clinical_content:
        raise HTTPException(status_code=400, detail="Provide clinical_note or discharge_summary")

    result = await translate(
        clinical_content=clinical_content,
        patient={"name": req.patient_name, "age": req.patient_age} if req.patient_name else None,
        target_language=req.language,
        reading_level=req.reading_level,
    )

    return {
        "status": "success",
        "patient_summary": result.get("module_output", {}).get("patient_summary", {}),
        "medications": result.get("module_output", {}).get("medications_explained", []),
        "care_instructions": result.get("module_output", {}).get("care_instructions", []),
        "warning_signs": result.get("module_output", {}).get("warning_signs", []),
        "faq": result.get("module_output", {}).get("faq", []),
        "follow_up": result.get("module_output", {}).get("follow_up_appointments", []),
    }


@router.get("/demo")
async def portal_demo_summary():
    """
    Demo endpoint — generates a sample patient-friendly health summary
    for testing the Patient Portal integration.
    """
    result = await translate(
        clinical_content={
            "clinical_note": "Patient diagnosed with community-acquired pneumonia (CAP). "
            "CXR shows left lower lobe infiltrate. Started on Azithromycin 500mg PO daily x5 days. "
            "Follow-up CXR in 4-6 weeks. Return precautions: worsening dyspnea, high fever >39C, "
            "hemoptysis, chest pain.",
        },
        patient={"name": "Patient", "age": "55"},
        target_language="en",
        reading_level="grade_5",
    )

    return {
        "status": "success",
        "data": result.get("module_output", {}),
    }
