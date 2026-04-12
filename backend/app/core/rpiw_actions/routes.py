from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db

from .schemas import (
    ClinicalNoteCreate, RpiwClinicalNoteOut,
    OrderCreate, RpiwOrderOut,
    PrescriptionCreate, RpiwPrescriptionOut,
    TaskCreate, RpiwTaskOut,
    VoiceCommandRequest, VoiceCommandResult, RpiwActionOut
)
from .services import RPIWActionService

router = APIRouter(prefix="/api/v1/rpiw-actions", tags=["RPIW - Clinical Action Engine"])

# ─── Standard Actions ──────────────────────────────────

@router.post("/notes", response_model=RpiwActionOut)
async def add_clinical_note(data: ClinicalNoteCreate, db: AsyncSession = Depends(get_db)):
    """Add a structured clinical note to the patient's record."""
    svc = RPIWActionService(db)
    action = await svc.add_clinical_note(data.model_dump())
    if action.status == "Failed":
         raise HTTPException(status_code=400, detail=action.validation_remarks)
    await db.commit()
    return action

@router.post("/orders", response_model=RpiwActionOut)
async def create_investigation_order(data: OrderCreate, db: AsyncSession = Depends(get_db)):
    """Order external clinical services (Labs, Radiology)."""
    svc = RPIWActionService(db)
    action = await svc.order_investigation(data.model_dump())
    if action.status == "Failed":
         raise HTTPException(status_code=400, detail=action.validation_remarks)
    await db.commit()
    return action

@router.post("/prescriptions", response_model=RpiwActionOut)
async def prescribe_medication(data: PrescriptionCreate, db: AsyncSession = Depends(get_db)):
    """Prescribe medication with safety validation."""
    svc = RPIWActionService(db)
    action = await svc.prescribe_medication(data.model_dump())
    if action.status == "Failed":
         raise HTTPException(status_code=400, detail=action.validation_remarks)
    await db.commit()
    return action

@router.post("/tasks", response_model=RpiwActionOut)
async def assign_staff_task(data: TaskCreate, db: AsyncSession = Depends(get_db)):
    """Assign a clinical task to a specific staff role."""
    svc = RPIWActionService(db)
    action = await svc.assign_task(data.model_dump())
    if action.status == "Failed":
         raise HTTPException(status_code=400, detail=action.validation_remarks)
    await db.commit()
    return action


# ─── NLP Engine (Voice to Structured Data) ──────────────────────────

@router.post("/voice-parse", response_model=VoiceCommandResult)
async def parse_voice_command(data: VoiceCommandRequest, db: AsyncSession = Depends(get_db)):
    """Convert clinician raw voice input transcript into a series of structured JSON action proposals."""
    svc = RPIWActionService(db)
    result = await svc.process_voice_command(data.transcript)
    return result

# Note: Once the frontend receives the VoiceCommandResult, it will display the structured proposals 
# (e.g., "Ready to order CBC" and "Prescribe Ceftriaxone").
# The user (clinician) then clicks "Confirm/Execute", mapping back individually to /orders and /prescriptions post endpoints.
