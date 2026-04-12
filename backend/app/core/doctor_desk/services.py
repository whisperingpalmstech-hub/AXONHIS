"""AI Doctor Desk & Intelligent EMR Engine — Business Logic Services"""
import uuid
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, case

from .models import (
    DoctorWorklist, ConsultationNote, DoctorClinicalTemplate,
    DoctorPrescription, DoctorDiagnosticOrder, DoctorClinicalSummary, FollowUpRecord, ConsultStatus
)
from .schemas import (
    DoctorWorklistCreate, ConsultationNoteInput, 
    DoctorClinicalTemplateCreate, PrescriptionInput, DiagnosticOrderInput,
    FollowUpRecordInput, AISuggestionOutput, PatientTimelineNode, PatientTimelineEMRViewer,
    ClinicalComplaintCreate, PatientMedicalHistoryCreate, ExaminationRecordCreate, DiagnosisRecordCreate, EMRConsultationVitalsCreate
)

class DoctorWorklistService:
    """Manages Doctor's Real-Time Patient Worklist"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_to_worklist(self, data: DoctorWorklistCreate, org_id: Optional[uuid.UUID] = None) -> DoctorWorklist:
        obj = DoctorWorklist(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_worklist(self, doctor_id: uuid.UUID) -> List[DoctorWorklist]:
        q = select(DoctorWorklist).where(DoctorWorklist.doctor_id == doctor_id).order_by(
            DoctorWorklist.queue_position.asc().nulls_last()
        )
        return list((await self.db.execute(q)).scalars().all())

    async def update_status(self, wl_id: uuid.UUID, status: ConsultStatus) -> DoctorWorklist:
        q = select(DoctorWorklist).where(DoctorWorklist.id == wl_id)
        wl = (await self.db.execute(q)).scalars().first()
        if not wl: return None
        wl.status = status.value
        now = datetime.utcnow()
        if status == ConsultStatus.in_consultation: wl.started_at = now
        elif status == ConsultStatus.completed: wl.completed_at = now
        await self.db.commit()
        await self.db.refresh(wl)
        return wl

class PatientTimelineEMRService:
    """Chronological Timeline compiler of patient history"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_timeline(self, patient_id: uuid.UUID) -> PatientTimelineEMRViewer:
        # In a real enterprise build, this gathers data from orders, results, lab sweeps, radiology logs.
        # We will dynamically compile it out of local logs + mock history
        nodes = []
        
        # 1. Past Consultations
        q_notes = select(ConsultationNote).where(ConsultationNote.visit_id != None).order_by(ConsultationNote.created_at.desc()) # This would typically join Visit/Patient but mocked by querying universally and doing basic
        # Since ConsultationNote lacks patient_id directly, we would normally join DoctorWorklist. 
        # Lets quickly inject simulated mock historical data representing the aggregated EMR model:
        nodes.append(PatientTimelineNode(
            node_type="visit", date="2025-10-18", title="Primary Care Encounter",
            details="Initial encounter for generalized fatigue and elevated BP."
        ))
        nodes.append(PatientTimelineNode(
            node_type="diagnosis", date="2025-10-18", title="Essential Hypertension",
            details="ICD-10: I10"
        ))
        nodes.append(PatientTimelineNode(
            node_type="rx", date="2025-10-18", title="Amlodipine 5mg",
            details="1 Tablet Oral Daily for 30 Days"
        ))
        nodes.append(PatientTimelineNode(
            node_type="lab_result", date="2025-10-20", title="Comprehensive Metabolic Panel",
            details="Result: Normal limits. Fasting Glucose: 98 mg/dL."
        ))

        return PatientTimelineEMRViewer(patient_id=patient_id, chronological_nodes=nodes)

class AIClinicalScribeEngine:
    """Automatically converts voice/base64 streams into structured sections"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_transcription_and_nlp(self, audio_data: str) -> dict:
        # Mock NLP Processing representing Speech-To-Text + Section Structuring Algorithms.
        return {
            "chief_complaint": "Patient presents with persistent dry cough and mild fever.",
            "history_present_illness": "Symptoms started 3 days ago. No relief with over-the-counter medication.",
            "physical_examination": "Temperature 38.0 C. Chest auscultation reveals mild crackles right lower lobe. HR 90 BPM.",
            "diagnosis": "Suspected lower respiratory tract infection / Bronchitis.",
            "plan": "Order CBC, start broad-spectrum oral antibiotic, review after 3 days."
        }

    async def save_note(self, data: ConsultationNoteInput, org_id: Optional[uuid.UUID] = None) -> ConsultationNote:
        q = select(ConsultationNote).where(ConsultationNote.visit_id == data.visit_id)
        note = (await self.db.execute(q)).scalars().first()
        if note:
            # update
            for k,v in data.model_dump().items():
                if v is not None: setattr(note, k, v)
        else:
            note = ConsultationNote(**data.model_dump(), org_id=org_id)
            self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

class VoicePrescriptionEngine:
    """Converts natural language commands to structured Rx form"""
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def parse_command(self, visit_id: uuid.UUID, doctor_id: uuid.UUID, text: str, org_id: Optional[uuid.UUID] = None) -> DoctorPrescription:
        """
        e.g. text: 'Paracetamol 500 mg twice daily for five days.'
        AI Entity Recognition Mock
        """
        rx_lower = text.lower()
        med = "Paracetamol" if "paracetamol" in rx_lower else "Amoxicillin" if "amox" in rx_lower else "Generic Medicine"
        strength = "500 mg" if "500" in text else "250 mg" if "250" in text else "Standard"
        frequency = "twice daily (BD)" if "twice" in rx_lower or "bd" in rx_lower else "Once Daily (OD)"
        duration = "5 days" if "five" in rx_lower or "5" in text else "7 days"
        
        rx = DoctorPrescription(
            visit_id=visit_id, doctor_id=doctor_id, medicine_name=med,
            strength=strength, dosage="1 Tablet", frequency=frequency,
            duration=duration, instructions=text, org_id=org_id
        )
        self.db.add(rx)
        await self.db.commit()
        await self.db.refresh(rx)
        return rx

class AIDiagnosisOrderSuggestionEngine:
    """Provides semantic decision support using symp/vitals vectors"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def recommend(self, symptoms: str) -> AISuggestionOutput:
        """Intelligent Rule-Engine for Clinical Decision Support.
        Analyzes keywords to suggest relevant diagnostics and assessments."""
        sym = symptoms.lower()
        
        # 1. Kidney Stone / Renal Colic (High Priority for Anita's current flow)
        if any(kw in sym for kw in ["kidney", "stone", "side pain", "flank pain", "back pain", "ureter"]):
            return AISuggestionOutput(
                suggested_diagnoses=["Renal Calculus (Kidney Stone)", "Ureteric Colic", "Urinary Tract Infection (UTI)"],
                recommended_lab_tests=["Urinalysis (Microscopic)", "S. Creatinine & Urea", "Calcium & Uric Acid", "Urine Culture"],
                recommended_imaging_studies=["USG KUB (Kidney, Ureter, Bladder)", "CT KUB (Plain)", "IVP (Intravenous Pyelogram)"]
            )
            
        # 2. Cardiac / Chest Pain
        elif "chest" in sym or "arm pain" in sym or "palpitations" in sym:
            return AISuggestionOutput(
                suggested_diagnoses=["Stable/Unstable Angina", "Myocardial Infarction", "Musculoskeletal Chest Pain"],
                recommended_lab_tests=["Cardiac Troponin T/I", "CK-MB", "Lipid Profile", "NT-proBNP"],
                recommended_imaging_studies=["12-Lead ECG", "Echocardiogram", "Treadmill Test (TMT)"]
            )
            
        # 3. Respiratory / Viral
        elif any(kw in sym for kw in ["fever", "cough", "breath", "throat", "chills"]):
            return AISuggestionOutput(
                suggested_diagnoses=["Viral Respiratory Infection", "Pneumonia", "Acute Bronchitis", "COVID-19"],
                recommended_lab_tests=["CBC with Differential", "CRP", "Influenza/COVID Panel", "Sputum Culture"],
                recommended_imaging_studies=["PA Chest X-Ray", "HRCT Thorax (If indicated)"]
            )

        # 4. Abdominal / Gastric
        elif any(kw in sym for kw in ["stomach", "abdomen", "gastric", "nausea", "vomit", "body pain"]):
            return AISuggestionOutput(
                suggested_diagnoses=["Acute Gastritis", "Gastroenteritis", "Cholelithiasis (Gallstones)", "Generalized Malaise"],
                recommended_lab_tests=["Liver Function Test (LFT)", "Serum Amylase/Lipase", "Stool Routine"],
                recommended_imaging_studies=["USG Whole Abdomen", "CT Abdomen (Contrast)"]
            )

        # 5. Default Fallback
        return AISuggestionOutput(
            suggested_diagnoses=["Undiagnosed Clinical Condition", "General Constitutional Symptoms"],
            recommended_lab_tests=["Comprehensive Metabolic Panel (CMP)", "Complete Blood Count (CBC)"],
            recommended_imaging_studies=["Review clinical history for targeted imaging"]
        )

class DiagnosticOrderingEngine:
    """Instantly transmits LIS/RIS orders marking progress logs"""
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def place_order(self, data: DiagnosticOrderInput, org_id: Optional[uuid.UUID] = None) -> DoctorDiagnosticOrder:
        order = DoctorDiagnosticOrder(**data.model_dump(), org_id=org_id)
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        
        # Integration hooks for Billing (CPOE -> RCM)
        try:
            from app.core.integration.services import ChargePostingService
            from app.core.integration.schemas import ChargePostingCreate
            from decimal import Decimal
            cp_service = ChargePostingService(self.db)
            
            # Figure out patient_id from worklist
            wl_stmt = select(DoctorWorklist.patient_id).where(DoctorWorklist.visit_id == data.visit_id).limit(1)
            patient_id = (await self.db.execute(wl_stmt)).scalars().first()
            
            if patient_id:
                # Post the charge into RCM immediately
                fee = Decimal("100.00") if data.order_type == "lab" else Decimal("500.00")
                await cp_service.post_charge(
                    data=ChargePostingCreate(
                        patient_id=patient_id,
                        encounter_type="opd",
                        encounter_id=data.visit_id,
                        service_name=f"{data.order_type.upper()} - {data.test_name}",
                        service_code=f"CPOE-{data.order_type.upper()[0:3]}",
                        service_group="diagnostics",
                        source_module="doctor_desk",
                        source_order_id=order.id,
                        quantity=1,
                        unit_price=fee,
                        is_stat=False
                    ),
                    posted_by=data.doctor_id,
                    posted_by_name="Doctor",
                    org_id=org_id or uuid.UUID(int=0)
                )
        except Exception as e:
            print("Failed to push to billing from CPOE:", e)
        
        return order


class ClinicalSummaryGenerator:
    """Assembles all Consultation actions into one coherent discharge envelope"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_summary(self, visit_id: uuid.UUID, doctor_id: uuid.UUID) -> DoctorClinicalSummary:
        # 0. Get Patient ID from worklist (needed for bridges)
        # 0. Get Patient ID from worklist (needed for bridges)
        # We MUST prioritize the patient who is currently 'in_consultation' 
        wl_stmt = select(DoctorWorklist.patient_id).where(
            and_(
                DoctorWorklist.visit_id == visit_id,
                DoctorWorklist.doctor_id == doctor_id
            )
        ).order_by(
            case((DoctorWorklist.status == "in_consultation", 0), else_=1).asc(),
            DoctorWorklist.created_at.desc()
        ).limit(1)
        patient_id = (await self.db.execute(wl_stmt)).scalars().first()

        # 1. Fetch Authored Notes
        note = (await self.db.execute(select(ConsultationNote).where(ConsultationNote.visit_id == visit_id))).scalars().first()
        # 2. Fetch Meds
        rxs = (await self.db.execute(select(DoctorPrescription).where(DoctorPrescription.visit_id == visit_id))).scalars().all()
        # 3. Fetch Orders
        orders = (await self.db.execute(select(DoctorDiagnosticOrder).where(DoctorDiagnosticOrder.visit_id == visit_id))).scalars().all()
        
        rx_list = [{"med": r.medicine_name, "freq": r.frequency, "dur": r.duration} for r in rxs]
        ord_list = [{"type": o.order_type, "test": o.test_name} for o in orders]
        
        val = {
            "chief_complaint": note.chief_complaint if note else "None documented",
            "diagnosis": note.diagnosis if note else "Pending",
            "prescriptions": rx_list,
            "orders": ord_list,
            "follow_up_instructions": note.plan if note else "Reviewed. Return if symptoms persist."
        }
        
        sumy_q = select(DoctorClinicalSummary).where(DoctorClinicalSummary.visit_id == visit_id)
        existing_sumy = (await self.db.execute(sumy_q)).scalars().first()
        
        pdf_path = f"/exports/doc_summary_{visit_id}.pdf"
        
        if existing_sumy:
            existing_sumy.summary_content = val
            existing_sumy.pdf_url = pdf_path
            sumy = existing_sumy
        else:
            sumy = DoctorClinicalSummary(
                visit_id=visit_id, doctor_id=doctor_id, summary_content=val, pdf_url=pdf_path
            )
            self.db.add(sumy)

        # ====== LIS INTEGRATION (AUTO-SYNC LAB ORDERS to PHLEBOTOMY) ======
        if patient_id:
            try:
                from app.core.lab.phlebotomy_engine.models import PhlebotomyWorklist
                
                for o in orders:
                    # Match both 'lab' and 'laboratory' (case-insensitive)
                    if o.order_type.lower() in ["lab_test", "lab", "laboratory"]:
                        # Check if already synced to Phlebotomy
                        exists_query = select(PhlebotomyWorklist).where(PhlebotomyWorklist.order_id == o.id)
                        exists = (await self.db.execute(exists_query)).scalars().first()
                        
                        if not exists:
                            wl_item = PhlebotomyWorklist(
                                id=uuid.uuid4(),
                                order_id=o.id,
                                order_item_id=o.id, # Uses the same ID as order_item for traceability
                                order_number=f"ORD-{str(o.id).split('-')[0].upper()}",
                                patient_id=patient_id,
                                visit_id=visit_id,
                                test_code="TEST-GENERIC",  
                                test_name=o.test_name,
                                sample_type="BLOOD",
                                priority="ROUTINE", # Default since is_urgent isn't on the model yet
                                status="PENDING_COLLECTION",
                                collection_location="OPD"
                            )
                            self.db.add(wl_item)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Phlebotomy Integration Error: {e}")
            
        await self.db.commit()
        await self.db.refresh(sumy)
        return sumy

class FollowUpCertificateManager:
    """Administers generated medical certs and logs referring dates"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(self, data: FollowUpRecordInput) -> FollowUpRecord:
        rec = FollowUpRecord(**data.model_dump())
        self.db.add(rec)
        await self.db.commit()
        await self.db.refresh(rec)
        return rec

# ── Extension for Universal EMR Subsystems ───────────────────────────

from .models import ClinicalComplaint, PatientMedicalHistory, ExaminationRecord, DiagnosisRecord, EMRConsultationVitals

class AdvancedEMRService:
    """Manages the full suite of clinical EMR parameters, diagnoses and history"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_complaint(self, data: ClinicalComplaintCreate, org_id: Optional[uuid.UUID] = None) -> ClinicalComplaint:
        obj = ClinicalComplaint(**data.model_dump(), org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_complaints(self, visit_id: uuid.UUID) -> List[ClinicalComplaint]:
        q = select(ClinicalComplaint).where(ClinicalComplaint.visit_id == visit_id)
        return list((await self.db.execute(q)).scalars().all())

    async def add_medical_history(self, recorded_by: uuid.UUID, data: PatientMedicalHistoryCreate, org_id: Optional[uuid.UUID] = None) -> PatientMedicalHistory:
        obj = PatientMedicalHistory(**data.model_dump(), recorded_by=recorded_by, org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_medical_history(self, patient_id: uuid.UUID) -> List[PatientMedicalHistory]:
        q = select(PatientMedicalHistory).where(PatientMedicalHistory.patient_id == patient_id)
        return list((await self.db.execute(q)).scalars().all())

    async def add_examination(self, recorded_by: uuid.UUID, data: ExaminationRecordCreate, org_id: Optional[uuid.UUID] = None) -> ExaminationRecord:
        obj = ExaminationRecord(**data.model_dump(), recorded_by=recorded_by, org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_examinations(self, visit_id: uuid.UUID) -> List[ExaminationRecord]:
        q = select(ExaminationRecord).where(ExaminationRecord.visit_id == visit_id)
        return list((await self.db.execute(q)).scalars().all())

    async def add_diagnosis(self, recorded_by: uuid.UUID, data: DiagnosisRecordCreate, org_id: Optional[uuid.UUID] = None) -> DiagnosisRecord:
        obj = DiagnosisRecord(**data.model_dump(), recorded_by=recorded_by, org_id=org_id)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        
        # Integration logic here if notifying CDSS or generating alerts
        return obj

    async def get_diagnoses(self, visit_id: uuid.UUID) -> List[DiagnosisRecord]:
        q = select(DiagnosisRecord).where(DiagnosisRecord.visit_id == visit_id)
        return list((await self.db.execute(q)).scalars().all())

    async def add_vitals(self, recorded_by: uuid.UUID, data: EMRConsultationVitalsCreate, org_id: Optional[uuid.UUID] = None) -> EMRConsultationVitals:
        obj = EMRConsultationVitals(**data.model_dump(), recorded_by=recorded_by, org_id=org_id)
        # Auto compute BMI
        if obj.height_cm and obj.weight_kg:
            try:
                h_m = float(obj.height_cm) / 100
                w_kg = float(obj.weight_kg)
                bmi = w_kg / (h_m * h_m)
                obj.bmi = f"{bmi:.1f}"
            except Exception:
                pass
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_vitals(self, visit_id: uuid.UUID) -> List[EMRConsultationVitals]:
        q = select(EMRConsultationVitals).where(EMRConsultationVitals.visit_id == visit_id)
        return list((await self.db.execute(q)).scalars().all())
