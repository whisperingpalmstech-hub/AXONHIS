"""AI Doctor Desk & Intelligent EMR Engine — Business Logic Services"""
import uuid
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from .models import (
    DoctorWorklist, ConsultationNote, DoctorClinicalTemplate,
    DoctorPrescription, DoctorDiagnosticOrder, DoctorClinicalSummary, FollowUpRecord, ConsultStatus
)
from .schemas import (
    DoctorWorklistCreate, ConsultationNoteInput, 
    DoctorClinicalTemplateCreate, PrescriptionInput, DiagnosticOrderInput,
    FollowUpRecordInput, AISuggestionOutput, PatientTimelineNode, PatientTimelineEMRViewer
)

class DoctorWorklistService:
    """Manages Doctor's Real-Time Patient Worklist"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_to_worklist(self, data: DoctorWorklistCreate) -> DoctorWorklist:
        obj = DoctorWorklist(**data.model_dump())
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

    async def save_note(self, data: ConsultationNoteInput) -> ConsultationNote:
        q = select(ConsultationNote).where(ConsultationNote.visit_id == data.visit_id)
        note = (await self.db.execute(q)).scalars().first()
        if note:
            # update
            for k,v in data.model_dump().items():
                if v is not None: setattr(note, k, v)
        else:
            note = ConsultationNote(**data.model_dump())
            self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

class VoicePrescriptionEngine:
    """Converts natural language commands to structured Rx form"""
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def parse_command(self, visit_id: uuid.UUID, doctor_id: uuid.UUID, text: str) -> DoctorPrescription:
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
            duration=duration, instructions=text
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
        # Mock Decision Tree Rules applied
        sym = symptoms.lower()
        if "fever" in sym and "cough" in sym:
            return AISuggestionOutput(
                suggested_diagnoses=["Viral Respiratory Infection", "Bronchitis", "Pneumonia"],
                recommended_lab_tests=["CBC with Differential", "CRP (C-Reactive Protein)"],
                recommended_imaging_studies=["PA Chest X-Ray"]
            )
        elif "pain" in sym and ("chest" in sym or "arm" in sym):
            return AISuggestionOutput(
                suggested_diagnoses=["Angina", "Myocardial Infarction", "GERD"],
                recommended_lab_tests=["Troponin I", "CK-MB", "Lipid Panel"],
                recommended_imaging_studies=["12-Lead ECG", "Echocardiogram"]
            )
        else:
            return AISuggestionOutput(
                suggested_diagnoses=["Undiagnosed Pathogen", "General Malaise"],
                recommended_lab_tests=["Comprehensive Metabolic Panel (CMP)"],
                recommended_imaging_studies=[]
            )

class DiagnosticOrderingEngine:
    """Instantly transmits LIS/RIS orders marking progress logs"""
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def place_order(self, data: DiagnosticOrderInput) -> DoctorDiagnosticOrder:
        order = DoctorDiagnosticOrder(**data.model_dump())
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order


class ClinicalSummaryGenerator:
    """Assembles all Consultation actions into one coherent discharge envelope"""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_summary(self, visit_id: uuid.UUID, doctor_id: uuid.UUID) -> DoctorClinicalSummary:
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
        
        sumy = DoctorClinicalSummary(
            visit_id=visit_id, doctor_id=doctor_id, summary_content=val, pdf_url=f"/exports/doc_summary_{visit_id}.pdf"
        )
        self.db.add(sumy)
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
