"""AI Doctor Desk & Intelligent EMR Engine — API Routes"""
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, case
from app.database import get_db
from app.dependencies import CurrentUser, DBSession

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
async def seed_doctor_worklist(data: DoctorWorklistCreate, db: DBSession, user: CurrentUser) -> DoctorWorklistOut:
    # Simulates Smart Queue -> Doctor Desk delegation
    svc = DoctorWorklistService(db)
    return await svc.add_to_worklist(data, org_id=user.org_id)

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
async def capture_clinical_assessment_note(data: ConsultationNoteInput, db: DBSession, user: CurrentUser) -> ConsultationNoteOut:
    svc = AIClinicalScribeEngine(db)
    # Inject org_id into data for save_note
    data_dict = data.model_dump()
    data_dict['org_id'] = user.org_id
    # We create a temporary object or just pass org_id differently
    # For simplicity, I'll update save_note to take org_id
    return await svc.save_note(data, org_id=user.org_id)

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
async def add_structured_medication(data: PrescriptionInput, db: DBSession, user: CurrentUser) -> PrescriptionOut:
    # Standard manual save
    from .models import DoctorPrescription
    rx = DoctorPrescription(**data.model_dump(), org_id=user.org_id)
    db.add(rx)
    await db.commit()
    await db.refresh(rx)
    
    # AUTO-BRIDGE: Push to Pharmacy Worklist
    try:
        from app.core.encounter_bridge import EncounterBridgeService
        from app.core.doctor_desk.models import DoctorWorklist
        
        # Simplified Lookup: Get the latest record for this doctor-visit pair
        wl_stmt = select(DoctorWorklist.patient_id).where(
            DoctorWorklist.visit_id == data.visit_id,
            DoctorWorklist.doctor_id == data.doctor_id
        ).order_by(DoctorWorklist.created_at.desc()).limit(1)
        
        patient_id = (await db.execute(wl_stmt)).scalars().first()
        
        if patient_id:
            bridge = EncounterBridgeService(db)
            await bridge.push_prescription_to_pharmacy(
                patient_id=patient_id,
                visit_id=data.visit_id,
                medication_name=data.medicine_name,
                dosage=data.dosage,
                frequency=data.frequency,
                duration=data.duration,
                org_id=user.org_id,
                doctor_id=data.doctor_id,
            )
            await db.commit()
            import logging
            logging.getLogger(__name__).info(f"[PHARMA-DEBUG] Pushed {data.medicine_name} for patient_id {patient_id}")
        else:
            import logging
            logging.getLogger(__name__).warning(f"[PHARMA-DEBUG] No patient found for visit_id {data.visit_id}")
            
    except Exception as e:
        import traceback
        import logging
        logging.getLogger(__name__).error(f"[PHARMA-BRIDGE-ERROR]: {str(e)}\n{traceback.format_exc()}")
    
    return rx

@router.get("/prescriptions", response_model=List[PrescriptionOut])
async def get_prescriptions(visit_id: Optional[uuid.UUID] = None, patient_id: Optional[uuid.UUID] = None, db: AsyncSession = Depends(get_db)):
    """Fetch prescriptions by visit_id. Used by RCM Billing to auto-capture pharmacy charges."""
    from .models import DoctorPrescription, DoctorWorklist
    if visit_id:
        stmt = select(DoctorPrescription).where(DoctorPrescription.visit_id == visit_id)
    elif patient_id:
        # Find all visit_ids for this patient from worklist, then get prescriptions
        wl_stmt = select(DoctorWorklist.visit_id).where(DoctorWorklist.patient_id == patient_id)
        visit_ids = list((await db.execute(wl_stmt)).scalars().all())
        if not visit_ids:
            return []
        stmt = select(DoctorPrescription).where(DoctorPrescription.visit_id.in_(visit_ids))
    else:
        stmt = select(DoctorPrescription).limit(50)
    return list((await db.execute(stmt)).scalars().all())

@router.post("/prescriptions/voice", response_model=PrescriptionOut)
async def add_voice_prescription(visit_id: uuid.UUID, data: VoicePrescriptionInput, db: DBSession, user: CurrentUser) -> PrescriptionOut:
    svc = VoicePrescriptionEngine(db)
    rx = await svc.parse_command(visit_id, data.doctor_id, data.voice_command_text, org_id=user.org_id)
    
    # ─── AUTO-BRIDGE: Push AI-Parsed Rx to Pharmacy ───────────────────────
    try:
        from app.core.encounter_bridge import EncounterBridgeService
        from app.core.doctor_desk.models import DoctorWorklist
        
        # Look up patient_id for this session
        wl_stmt = select(DoctorWorklist.patient_id).where(
            DoctorWorklist.visit_id == visit_id,
            DoctorWorklist.doctor_id == data.doctor_id
        ).order_by(DoctorWorklist.created_at.desc()).limit(1)
        
        patient_id = (await db.execute(wl_stmt)).scalars().first()
        
        if patient_id:
            bridge = EncounterBridgeService(db)
            await bridge.push_prescription_to_pharmacy(
                patient_id=patient_id,
                visit_id=visit_id,
                medication_name=rx.medicine_name,
                dosage=rx.dosage,
                frequency=rx.frequency,
                duration=rx.duration,
                org_id=user.org_id,
                doctor_id=data.doctor_id,
            )
            await db.commit()
            import logging
            logging.getLogger(__name__).info(f"[PHARMA-VOICE-DEBUG] Pushed {rx.medicine_name} for Anita ({patient_id})")
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Voice Pharmacy bridge failed: {e}")
        
    return rx

# ── 5. AI Diagnosis & Order Suggestion Engine ───────────────────────────────

@router.post("/ai/suggestions", response_model=AISuggestionOutput)
async def query_diagnosis_decision_engine(data: AISuggestionEngineInput, db: AsyncSession = Depends(get_db)):
    svc = AIDiagnosisOrderSuggestionEngine(db)
    return await svc.recommend(data.symptoms)

# ── 7. Diagnostic Ordering Engine ───────────────────────────────────────────

@router.post("/orders", response_model=DiagnosticOrderOut)
async def transmit_diagnostic_order(data: DiagnosticOrderInput, db: DBSession, user: CurrentUser) -> DiagnosticOrderOut:
    svc = DiagnosticOrderingEngine(db)
    order = await svc.place_order(data, org_id=user.org_id)
    
    # ─── AUTO-BRIDGE: Push to LIS ──────────────────────────────────────────
    try:
        from app.core.encounter_bridge import EncounterBridgeService
        from app.core.doctor_desk.models import DoctorWorklist
        
        # 1. Get Patient ID from worklist using visit_id
        # We MUST prioritize the patient who is currently 'in_consultation' 
        # to handle cases where multiple patients share a generic visit_id (like 0000... zero UUID)
        wl_stmt = select(DoctorWorklist.patient_id).where(
            and_(
                DoctorWorklist.visit_id == data.visit_id,
                DoctorWorklist.doctor_id == data.doctor_id
            )
        ).order_by(
            # Smart Priority: 1. Current Patients, 2. Most Recent
            case((DoctorWorklist.status == "in_consultation", 0), else_=1).asc(),
            DoctorWorklist.created_at.desc()
        ).limit(1)
        
        patient_id = (await db.execute(wl_stmt)).scalars().first()
        
        if patient_id:
            bridge = EncounterBridgeService(db)
            await bridge.push_diagnostic_to_lis(
                patient_id=patient_id,
                encounter_id=data.visit_id, # visit_id is encounter_id in this context
                test_name=data.test_name,
                doctor_id=data.doctor_id,
                org_id=user.org_id,
                priority=data.order_type # Using order_type as a priority proxy if needed
            )
            await db.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"LIS bridge failed: {e}")
        
    return order

@router.get("/orders", response_model=List[DiagnosticOrderOut])
async def get_diagnostic_orders(visit_id: Optional[uuid.UUID] = None, patient_id: Optional[uuid.UUID] = None, db: AsyncSession = Depends(get_db)):
    """Fetch diagnostic orders by visit_id or patient_id. Used by RCM Billing to auto-capture lab/radiology charges."""
    from .models import DoctorDiagnosticOrder, DoctorWorklist
    if visit_id:
        stmt = select(DoctorDiagnosticOrder).where(DoctorDiagnosticOrder.visit_id == visit_id)
    elif patient_id:
        wl_stmt = select(DoctorWorklist.visit_id).where(DoctorWorklist.patient_id == patient_id)
        visit_ids = list((await db.execute(wl_stmt)).scalars().all())
        if not visit_ids:
            return []
        stmt = select(DoctorDiagnosticOrder).where(DoctorDiagnosticOrder.visit_id.in_(visit_ids))
    else:
        stmt = select(DoctorDiagnosticOrder).limit(50)
    return list((await db.execute(stmt)).scalars().all())

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


# ── Extension for Universal EMR Subsystems ───────────────────────────

from .schemas import (
    ClinicalComplaintCreate, ClinicalComplaintOut,
    PatientMedicalHistoryCreate, PatientMedicalHistoryOut,
    ExaminationRecordCreate, ExaminationRecordOut,
    DiagnosisRecordCreate, DiagnosisRecordOut,
    EMRConsultationVitalsCreate, EMRConsultationVitalsOut
)
from .services import AdvancedEMRService

@router.post("/advanced/complaints", response_model=ClinicalComplaintOut)
async def add_clinical_complaint(data: ClinicalComplaintCreate, db: DBSession, user: CurrentUser):
    svc = AdvancedEMRService(db)
    return await svc.add_complaint(data, org_id=user.org_id)

@router.get("/advanced/complaints/{visit_id}", response_model=List[ClinicalComplaintOut])
async def get_clinical_complaints(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = AdvancedEMRService(db)
    return await svc.get_complaints(visit_id)

@router.post("/advanced/medical-history", response_model=PatientMedicalHistoryOut)
async def add_medical_history(data: PatientMedicalHistoryCreate, db: DBSession, user: CurrentUser):
    svc = AdvancedEMRService(db)
    return await svc.add_medical_history(recorded_by=user.id, data=data, org_id=user.org_id)

@router.get("/advanced/medical-history/{patient_id}", response_model=List[PatientMedicalHistoryOut])
async def get_medical_history(patient_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = AdvancedEMRService(db)
    return await svc.get_medical_history(patient_id)

@router.post("/advanced/examinations", response_model=ExaminationRecordOut)
async def add_examination_record(data: ExaminationRecordCreate, db: DBSession, user: CurrentUser):
    svc = AdvancedEMRService(db)
    return await svc.add_examination(recorded_by=user.id, data=data, org_id=user.org_id)

@router.get("/advanced/examinations/{visit_id}", response_model=List[ExaminationRecordOut])
async def get_examination_records(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = AdvancedEMRService(db)
    return await svc.get_examinations(visit_id)

@router.post("/advanced/diagnoses", response_model=DiagnosisRecordOut)
async def add_diagnosis_record(data: DiagnosisRecordCreate, db: DBSession, user: CurrentUser):
    svc = AdvancedEMRService(db)
    return await svc.add_diagnosis(recorded_by=user.id, data=data, org_id=user.org_id)

@router.get("/advanced/diagnoses/{visit_id}", response_model=List[DiagnosisRecordOut])
async def get_diagnosis_records(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = AdvancedEMRService(db)
    return await svc.get_diagnoses(visit_id)

@router.post("/advanced/vitals", response_model=EMRConsultationVitalsOut)
async def add_consultation_vitals(data: EMRConsultationVitalsCreate, db: DBSession, user: CurrentUser):
    svc = AdvancedEMRService(db)
    return await svc.add_vitals(recorded_by=user.id, data=data, org_id=user.org_id)

@router.get("/advanced/vitals/{visit_id}", response_model=List[EMRConsultationVitalsOut])
async def get_consultation_vitals(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = AdvancedEMRService(db)
    return await svc.get_vitals(visit_id)
