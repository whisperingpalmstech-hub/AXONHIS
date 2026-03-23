"""OPD Nursing Clinical Triage Engine — Business Logic Services"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from .models import (
    NursingWorklist, NursingVitals, NursingAssessment,
    NursingTemplate, NursingDocumentUpload, TriagePriorityUpdate, TriageStatus
)
from .schemas import (
    NursingWorklistCreate, NursingVitalsCreate, NursingAssessmentCreate, DocumentUploadCreate, DoctorNotificationContext
)

class AbnormalVitalsAlertEngine:
    """Real-time abnormal clinical indicator detection"""
    
    @staticmethod
    def evaluate_vitals(v: NursingVitalsCreate) -> Optional[str]:
        triggers = []
        if v.oxygen_saturation_spo2 is not None and v.oxygen_saturation_spo2 < 92:
            triggers.append(f"SpO2 severely low ({v.oxygen_saturation_spo2}%)")
        if v.blood_pressure_systolic is not None and v.blood_pressure_systolic > 180:
            triggers.append(f"Sys BP severely high ({v.blood_pressure_systolic})")
        if v.blood_pressure_diastolic is not None and v.blood_pressure_diastolic > 110:
            triggers.append(f"Dia BP severely high ({v.blood_pressure_diastolic})")
        if v.heart_rate is not None and v.heart_rate > 120:
            triggers.append(f"Heart Rate high ({v.heart_rate} bpm)")
        if v.temperature_celsius is not None and v.temperature_celsius > 39.0:
            triggers.append(f"High Fever ({v.temperature_celsius}°C)")
            
        if triggers:
            return " | ".join(triggers)
        return None


class VitalsCaptureEngine:
    """Structured vital signs processor & calculator"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_vitals(self, data: NursingVitalsCreate) -> NursingVitals:
        # BMI Auto calculation
        calculated_bmi = None
        if data.height_cm and data.weight_kg and data.height_cm > 0:
            height_m = data.height_cm / 100.0
            calculated_bmi = round(data.weight_kg / (height_m * height_m), 1)

        vitals = NursingVitals(
            visit_id=data.visit_id, patient_id=data.patient_id,
            blood_pressure_systolic=data.blood_pressure_systolic,
            blood_pressure_diastolic=data.blood_pressure_diastolic,
            heart_rate=data.heart_rate, respiratory_rate=data.respiratory_rate,
            temperature_celsius=data.temperature_celsius,
            oxygen_saturation_spo2=data.oxygen_saturation_spo2,
            height_cm=data.height_cm, weight_kg=data.weight_kg, bmi=calculated_bmi,
            blood_glucose=data.blood_glucose, pain_score=data.pain_score, gcs_score=data.gcs_score
        )
        self.db.add(vitals)
        
        # Check abnormal vitals
        trigger = AbnormalVitalsAlertEngine.evaluate_vitals(data)
        if trigger:
            # Upgrade visit priority to exactly Emergency/Priority.
            # We log this in TriagePriorityUpdates
            wl = (await self.db.execute(select(NursingWorklist).where(NursingWorklist.visit_id == data.visit_id))).scalars().first()
            prev = "normal"
            if wl:
                prev = wl.priority_level
                wl.priority_level = "priority"
                
            priority_update = TriagePriorityUpdate(
                visit_id=data.visit_id, previous_priority=prev, new_priority="priority",
                trigger_reason=trigger, vitals_snapshot=data.model_dump(mode="json", exclude_none=True)
            )
            self.db.add(priority_update)

        await self.db.commit()
        await self.db.refresh(vitals)
        return vitals


class NursingWorklistService:
    """Patient Arrival, Queue Call & Workflow Triage Status Logic"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_to_worklist(self, data: NursingWorklistCreate) -> NursingWorklist:
        wl = NursingWorklist(
            visit_id=data.visit_id, patient_id=data.patient_id, priority_level=data.priority_level
        )
        self.db.add(wl)
        await self.db.commit()
        await self.db.refresh(wl)
        return wl

    async def update_status(self, wl_id: uuid.UUID, status: TriageStatus) -> NursingWorklist:
        wl = (await self.db.execute(select(NursingWorklist).where(NursingWorklist.id == wl_id))).scalars().first()
        if not wl: return None
        
        wl.triage_status = status.value
        now = datetime.utcnow()
        if status == TriageStatus.in_progress: wl.started_at = now
        elif status == TriageStatus.completed: wl.completed_at = now
        
        await self.db.commit()
        await self.db.refresh(wl)
        return wl


class AssessmentHistoryService:
    """Provides Structured Content Templates and Saves Assessments"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_assessment(self, data: NursingAssessmentCreate) -> NursingAssessment:
        assess = NursingAssessment(**data.model_dump())
        self.db.add(assess)
        await self.db.commit()
        await self.db.refresh(assess)
        return assess

    async def get_templates(self) -> List[NursingTemplate]:
        q = select(NursingTemplate).where(NursingTemplate.is_active == True)
        return (await self.db.execute(q)).scalars().all()


class DocumentUploadSystem:
    """Manages file metadata to store in EHR repo"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_document(self, data: DocumentUploadCreate) -> NursingDocumentUpload:
        doc = NursingDocumentUpload(**data.model_dump())
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc


class TriageNotificationService:
    """Pulls everything together for Doctor Desk notification package"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def prepare_doctor_context(self, visit_id: uuid.UUID) -> Optional[DoctorNotificationContext]:
        vitals = (await self.db.execute(
            select(NursingVitals).where(NursingVitals.visit_id == visit_id).order_by(NursingVitals.recorded_at.desc())
        )).scalars().first()
        
        assess = (await self.db.execute(
            select(NursingAssessment).where(NursingAssessment.visit_id == visit_id).order_by(NursingAssessment.recorded_at.desc())
        )).scalars().first()
        
        docs = (await self.db.execute(
            select(NursingDocumentUpload).where(NursingDocumentUpload.visit_id == visit_id)
        )).scalars().all()
        
        wl = (await self.db.execute(select(NursingWorklist).where(NursingWorklist.visit_id == visit_id))).scalars().first()
        
        return DoctorNotificationContext(
            visit_id=visit_id,
            vitals_summary=vitals,
            assessment_notes=assess,
            documents=docs,
            priority_flag=wl.priority_level if wl else "normal"
        )
