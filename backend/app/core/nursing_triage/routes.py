"""OPD Nursing Clinical Triage Engine — API Routes"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.dependencies import CurrentUser

from .models import NursingWorklist, TriageStatus, NursingTemplate
from .schemas import (
    NursingWorklistCreate, NursingWorklistOut,
    NursingVitalsCreate, NursingVitalsOut,
    NursingAssessmentCreate, NursingAssessmentOut,
    NursingTemplateOut,
    DocumentUploadCreate, DocumentUploadOut,
    DoctorNotificationContext
)
from .services import (
    NursingWorklistService, VitalsCaptureEngine,
    AssessmentHistoryService, DocumentUploadSystem, TriageNotificationService
)

router = APIRouter(prefix="/nursing-triage", tags=["OPD Nursing Triage"])

# ── 1. Nursing Worklist Dashboard ───────────────────────────────────────────

@router.get("/worklist", response_model=List[NursingWorklistOut])
async def get_nursing_worklist(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    # Returns the active list of patients waiting for triage
    q = select(NursingWorklist).where(NursingWorklist.org_id == user.org_id).order_by(NursingWorklist.created_at.asc())
    return (await db.execute(q)).scalars().all()

@router.post("/worklist", response_model=NursingWorklistOut)
async def add_patient_to_nursing_queue(data: NursingWorklistCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    data.org_id = user.org_id
    svc = NursingWorklistService(db)
    return await svc.add_to_worklist(data)

@router.put("/worklist/{wl_id}/status")
async def update_worklist_status(wl_id: uuid.UUID, status: str, db: AsyncSession = Depends(get_db)):
    status_enum = TriageStatus(status)
    svc = NursingWorklistService(db)
    wl = await svc.update_status(wl_id, status_enum)
    if not wl: raise HTTPException(404, "Worklist item not found")
    return {"status": "ok", "mapped_status": wl.triage_status}

# ── 2. Vitals Capture & Alert Engine ────────────────────────────────────────

@router.post("/vitals", response_model=NursingVitalsOut)
async def record_patient_vitals(data: NursingVitalsCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    data.org_id = user.org_id
    svc = VitalsCaptureEngine(db)
    # The record_vitals method automatically runs the AbnormalVitalsAlertEngine
    vitals = await svc.record_vitals(data)
    return vitals

# ── 3. Clinical Templates & Assessments ─────────────────────────────────────

@router.get("/templates", response_model=List[NursingTemplateOut])
async def get_nursing_templates(db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(NursingTemplate).where(NursingTemplate.is_active==True))).scalars().all()

@router.post("/assessments", response_model=NursingAssessmentOut)
async def record_nursing_assessment(data: NursingAssessmentCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    data.org_id = user.org_id
    svc = AssessmentHistoryService(db)
    return await svc.save_assessment(data)

# ── 4. Document Management ──────────────────────────────────────────────────

@router.post("/documents", response_model=DocumentUploadOut)
async def attach_nursing_document(data: DocumentUploadCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    data.org_id = user.org_id
    svc = DocumentUploadSystem(db)
    return await svc.register_document(data)

# ── 5. Real-Time Doctor Notification ────────────────────────────────────────

@router.get("/doctor-context/{visit_id}", response_model=DoctorNotificationContext)
async def compile_doctor_desk_context(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Called by Doctor Desk to retrieve structured context right before encounter"""
    svc = TriageNotificationService(db)
    ctx = await svc.prepare_doctor_context(visit_id)
    if not ctx: raise HTTPException(404, "No context compiled for this visit yet.")
    return ctx
