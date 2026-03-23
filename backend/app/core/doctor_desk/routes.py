"""AI Doctor Desk & Intelligent EMR Engine — API Routes"""
import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db

from .models import ConsultStatus
from .schemas import (
    DoctorWorklistCreate, DoctorWorklistOut,
    ConsultationNoteInput, ConsultationNoteOut, ScribeAudioInput,
    AISuggestionEngineInput, AISuggestionOutput,
    DiagnosticOrderInput, DiagnosticOrderOut,
    PrescriptionInput, PrescriptionOut, VoicePrescriptionInput,
    ClinicalSummaryOut, FollowUpRecordInput, FollowUpRecordOut,
    PatientTimelineEMRViewer
)
from .services import (
    DoctorWorklistService, PatientTimelineEMRService, AIClinicalScribeEngine,
    VoicePrescriptionEngine, AIDiagnosisOrderSuggestionEngine, DiagnosticOrderingEngine,
    ClinicalSummaryGenerator, FollowUpCertificateManager
)

router = APIRouter(prefix="/doctor-desk", tags=["Doctor Desk (EMR)"])

# ── 1. Doctor Worklist Dashboard ───────────────────────────────────────────

@router.get("/worklist/{doctor_id}", response_model=List[DoctorWorklistOut])
async def get_doctor_worklist(doctor_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = DoctorWorklistService(db)
    return await svc.get_worklist(doctor_id)

@router.post("/worklist", response_model=DoctorWorklistOut)
async def seed_doctor_worklist(data: DoctorWorklistCreate, db: AsyncSession = Depends(get_db)):
    # Simulates Smart Queue -> Doctor Desk delegation
    svc = DoctorWorklistService(db)
    return await svc.add_to_worklist(data)

@router.put("/worklist/{wl_id}/status")
async def update_consultation_status(wl_id: uuid.UUID, status: str, db: AsyncSession = Depends(get_db)):
    svc = DoctorWorklistService(db)
    wl = await svc.update_status(wl_id, ConsultStatus(status))
    if not wl: raise HTTPException(404, "Worklist item not found")
    return {"status": "ok"}

# ── 2. Patient Timeline EMR Viewer ──────────────────────────────────────────

@router.get("/timeline/{patient_id}", response_model=PatientTimelineEMRViewer)
async def fetch_historical_patient_timeline(patient_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = PatientTimelineEMRService(db)
    return await svc.get_timeline(patient_id)

# ── 3. AI Clinical Scribe Engine ────────────────────────────────────────────

@router.post("/scribe", response_model=ConsultationNoteOut)
async def capture_clinical_assessment_note(data: ConsultationNoteInput, db: AsyncSession = Depends(get_db)):
    svc = AIClinicalScribeEngine(db)
    return await svc.save_note(data)

@router.post("/scribe/transcribe")
async def nlp_voice_transcription(data: ScribeAudioInput, db: AsyncSession = Depends(get_db)):
    # Mocking NLP base64 analysis payload return
    return {
        "status": "success",
        "structured_note": {
           "chief_complaint": "Extracted via AI: Patient reports recurring migraines.",
           "history_present_illness": "Starts from the neck up to the left temple. Occurs weekly.",
           "plan": "Review triggers. MRI head if no improvement after 1 month."
        }
    }

# ── 4 & 8. Voice & Structured Prescription Engine ───────────────────────────

@router.post("/prescriptions", response_model=PrescriptionOut)
async def add_structured_medication(data: PrescriptionInput, db: AsyncSession = Depends(get_db)):
    # Standard manual save
    from .models import DoctorPrescription
    rx = DoctorPrescription(**data.model_dump())
    db.add(rx)
    await db.commit()
    await db.refresh(rx)
    return rx

@router.post("/prescriptions/voice", response_model=PrescriptionOut)
async def add_voice_prescription(visit_id: uuid.UUID, data: VoicePrescriptionInput, db: AsyncSession = Depends(get_db)):
    svc = VoicePrescriptionEngine(db)
    return await svc.parse_command(visit_id, data.doctor_id, data.voice_command_text)

# ── 5. AI Diagnosis & Order Suggestion Engine ───────────────────────────────

@router.post("/ai/suggestions", response_model=AISuggestionOutput)
async def query_diagnosis_decision_engine(data: AISuggestionEngineInput, db: AsyncSession = Depends(get_db)):
    svc = AIDiagnosisOrderSuggestionEngine(db)
    return await svc.recommend(data.symptoms)

# ── 7. Diagnostic Ordering Engine ───────────────────────────────────────────

@router.post("/orders", response_model=DiagnosticOrderOut)
async def transmit_diagnostic_order(data: DiagnosticOrderInput, db: AsyncSession = Depends(get_db)):
    svc = DiagnosticOrderingEngine(db)
    return await svc.place_order(data)

# ── 9. Clinical Summary Generator ───────────────────────────────────────────

@router.post("/summary/{visit_id}", response_model=ClinicalSummaryOut)
async def compile_visit_discharge_summary(visit_id: uuid.UUID, doctor_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = ClinicalSummaryGenerator(db)
    return await svc.generate_summary(visit_id, doctor_id)

# ── 10. Follow-Up & Certificate Management ──────────────────────────────────

@router.post("/follow-ups", response_model=FollowUpRecordOut)
async def log_follow_up_action(data: FollowUpRecordInput, db: AsyncSession = Depends(get_db)):
    svc = FollowUpCertificateManager(db)
    return await svc.log_action(data)
