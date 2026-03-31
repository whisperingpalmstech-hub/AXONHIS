"""OPD Visit Intelligence Engine — Service Layer"""
import uuid
import re
from datetime import datetime, date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from .models import (
    VisitMaster, VisitComplaint, VisitClassification,
    VisitDoctorRecommendation, VisitQuestionnaireTemplate,
    VisitQuestionnaireResponse, VisitContextSnapshot,
    MultiVisitRule, VisitAnalyticsSnapshot,
    VisitStatus, PriorityTag, ClassificationCategory,
)
from .schemas import (
    VisitCreate, VisitUpdate, ComplaintCreate, ClassificationCreate,
    ClassificationOverride, DoctorSelectionUpdate,
    QuestionnaireTemplateCreate, QuestionnaireResponseCreate,
    MultiVisitRuleCreate, VisitDashboardSummary,
)


# ── Symptom → ICPC Mapping (Rule-based AI) ───────────────────────────────────

SYMPTOM_ICPC_MAP = {
    "chest pain": {"code": "K01", "label": "Chest pain", "severity": 8},
    "breathlessness": {"code": "R02", "label": "Shortness of breath", "severity": 8},
    "dizziness": {"code": "N17", "label": "Vertigo/dizziness", "severity": 5},
    "headache": {"code": "N01", "label": "Headache", "severity": 4},
    "fever": {"code": "A03", "label": "Fever", "severity": 5},
    "cough": {"code": "R05", "label": "Cough", "severity": 3},
    "abdominal pain": {"code": "D01", "label": "Abdominal pain", "severity": 5},
    "back pain": {"code": "L02", "label": "Back symptom", "severity": 4},
    "skin rash": {"code": "S06", "label": "Rash localised", "severity": 3},
    "joint pain": {"code": "L20", "label": "Joint symptom", "severity": 4},
    "vomiting": {"code": "D10", "label": "Vomiting", "severity": 5},
    "nausea": {"code": "D09", "label": "Nausea", "severity": 3},
    "diarrhea": {"code": "D11", "label": "Diarrhoea", "severity": 4},
    "sore throat": {"code": "R21", "label": "Throat symptom", "severity": 3},
    "eye pain": {"code": "F01", "label": "Eye pain", "severity": 4},
    "ear pain": {"code": "H01", "label": "Ear pain", "severity": 3},
    "urinary problem": {"code": "U01", "label": "Dysuria", "severity": 4},
    "loss of consciousness": {"code": "A06", "label": "Fainting/syncope", "severity": 9},
    "bleeding": {"code": "A10", "label": "Bleeding", "severity": 7},
    "weakness": {"code": "A04", "label": "Weakness/tiredness", "severity": 4},
    "anxiety": {"code": "P01", "label": "Anxiety", "severity": 4},
    "depression": {"code": "P03", "label": "Feeling depressed", "severity": 5},
    "weight loss": {"code": "T08", "label": "Weight loss", "severity": 5},
    "palpitations": {"code": "K04", "label": "Palpitations", "severity": 6},
}

SYMPTOM_TO_SPECIALTY = {
    "chest pain": "Cardiology", "palpitations": "Cardiology",
    "breathlessness": "Pulmonology", "cough": "Pulmonology",
    "headache": "Neurology", "dizziness": "Neurology",
    "loss of consciousness": "Emergency Medicine",
    "skin rash": "Dermatology", "joint pain": "Orthopedics",
    "back pain": "Orthopedics", "abdominal pain": "Gastroenterology",
    "vomiting": "Gastroenterology", "diarrhea": "Gastroenterology",
    "eye pain": "Ophthalmology", "ear pain": "ENT",
    "sore throat": "ENT", "urinary problem": "Urology",
    "anxiety": "Psychiatry", "depression": "Psychiatry",
    "fever": "General Medicine", "weakness": "General Medicine",
    "bleeding": "General Surgery", "nausea": "General Medicine",
    "weight loss": "Endocrinology",
}

EMERGENCY_KEYWORDS = {
    "chest pain", "breathlessness", "loss of consciousness",
    "bleeding", "severe pain", "seizure", "stroke",
}

PRIORITY_KEYWORDS = {
    "palpitations", "high fever", "vomiting blood", "severe headache",
    "fainting", "difficulty breathing", "chest tightness",
}


def _generate_visit_id() -> str:
    now = datetime.utcnow()
    return f"V{now.strftime('%y%m%d')}{str(uuid.uuid4().int)[:6]}"


def _generate_encounter_id() -> str:
    now = datetime.utcnow()
    return f"E{now.strftime('%y%m%d')}{str(uuid.uuid4().int)[:6]}"


# ═════════════════════════════════════════════════════════════════════════════
# 1. VISIT CREATION SERVICE
# ═════════════════════════════════════════════════════════════════════════════

class VisitCreationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_visit(self, data: VisitCreate, org_id: uuid.UUID | None = None) -> VisitMaster:
        # Create a real Encounter record for inter-module linking
        from app.core.encounter_bridge import EncounterBridgeService
        bridge = EncounterBridgeService(self.db)
        encounter = await bridge.create_encounter_for_visit(
            patient_id=data.patient_id,
            org_id=org_id,
            doctor_id=data.doctor_id,
            chief_complaint=None,
            encounter_type="OPD"
        )
        
        visit = VisitMaster(
            visit_id=_generate_visit_id(),
            encounter_id=str(encounter.id),  # Link to real Encounter
            patient_id=data.patient_id,
            patient_uhid=data.patient_uhid,
            visit_type=data.visit_type,
            visit_source=data.visit_source,
            specialty=data.specialty,
            doctor_id=data.doctor_id,
            department=data.department,
            clinic_location=data.clinic_location,
            referral_type=data.referral_type,
            referral_source=data.referral_source,
            payment_entitlement=data.payment_entitlement,
            priority_tag=data.priority_tag,
            is_follow_up=data.is_follow_up,
            parent_visit_id=data.parent_visit_id,
            appointment_id=data.appointment_id,
            status=VisitStatus.created,
            org_id=org_id
        )
        self.db.add(visit)
        
        # Phase 23 - Auto-initialize Billing via Bridge
        try:
            # We use doctor_id as a fallback for 'generated_by'
            sys_admin_id = data.doctor_id or uuid.uuid4() 
            await bridge.initialize_bill(
                patient_id=data.patient_id,
                visit_id=encounter.id,
                generated_by=sys_admin_id,
                org_id=org_id,
                encounter_type="OPD"
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[BRIDGE] Billing initialization failed: {e}")

        await self.db.commit()
        await self.db.refresh(visit)
        return visit

    async def get_visit(self, visit_id: uuid.UUID, org_id: uuid.UUID | None = None) -> Optional[VisitMaster]:
        stmt = select(VisitMaster).where(VisitMaster.id == visit_id)
        if org_id:
            stmt = stmt.where(VisitMaster.org_id == org_id)
        r = await self.db.execute(stmt)
        return r.scalar_one_or_none()

    async def update_visit(self, visit_id: uuid.UUID, data: VisitUpdate, org_id: uuid.UUID | None = None) -> Optional[VisitMaster]:
        visit = await self.get_visit(visit_id, org_id=org_id)
        if not visit:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(visit, k, v)
        visit.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(visit)
        return visit

    async def list_visits(
        self, patient_id: Optional[uuid.UUID] = None,
        doctor_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        visit_date: Optional[str] = None,
        department: Optional[str] = None,
        priority_tag: Optional[str] = None,
        org_id: uuid.UUID | None = None,
    ) -> list[VisitMaster]:
        q = select(VisitMaster).order_by(VisitMaster.visit_date_time.desc())
        if org_id:
            q = q.where(VisitMaster.org_id == org_id)
        if patient_id:
            q = q.where(VisitMaster.patient_id == patient_id)
        if doctor_id:
            q = q.where(VisitMaster.doctor_id == doctor_id)
        if status:
            q = q.where(VisitMaster.status == status)
        if visit_date:
            d = date.fromisoformat(visit_date)
            q = q.where(func.date(VisitMaster.visit_date_time) == d)
        if department:
            q = q.where(VisitMaster.department == department)
        if priority_tag:
            q = q.where(VisitMaster.priority_tag == priority_tag)
        r = await self.db.execute(q.limit(200))
        return list(r.scalars().all())

    async def get_todays_queue(self, doctor_id: uuid.UUID, org_id: uuid.UUID | None = None) -> list[VisitMaster]:
        today = date.today()
        q = (select(VisitMaster)
             .where(VisitMaster.doctor_id == doctor_id)
             .where(func.date(VisitMaster.visit_date_time) == today)
             .where(VisitMaster.status.in_([
                 VisitStatus.created, VisitStatus.triage_pending,
                 VisitStatus.in_queue, VisitStatus.with_nurse,
                 VisitStatus.with_doctor,
             ]))
             .order_by(VisitMaster.visit_date_time))
        if org_id:
            q = q.where(VisitMaster.org_id == org_id)
        r = await self.db.execute(q)
        return list(r.scalars().all())


# ═════════════════════════════════════════════════════════════════════════════
# 2. AI COMPLAINT CAPTURE SERVICE
# ═════════════════════════════════════════════════════════════════════════════

class ComplaintCaptureService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def capture_complaint(self, data: ComplaintCreate, org_id: uuid.UUID | None = None) -> VisitComplaint:
        text = data.raw_complaint_text.lower().strip()

        # Check visit ownership
        svc = VisitCreationService(self.db)
        visit = await svc.get_visit(data.visit_id, org_id=org_id)
        if not visit:
            raise ValueError("Visit not found in your organization")

        # Extract symptoms
        symptoms = []
        keywords = []
        icpc_codes = []
        max_severity = 0.0

        for symptom, info in SYMPTOM_ICPC_MAP.items():
            if symptom in text:
                symptoms.append(symptom)
                keywords.append(info["label"])
                icpc_codes.append({"code": info["code"], "label": info["label"]})
                max_severity = max(max_severity, info["severity"])

        # If no known symptoms matched, do basic keyword extraction
        if not symptoms:
            words = re.findall(r'\b[a-z]{3,}\b', text)
            medical_words = [w for w in words if w not in {
                "the", "and", "have", "has", "been", "with", "for",
                "from", "this", "that", "very", "much", "some",
            }]
            symptoms = medical_words[:5]
            max_severity = 3.0

        complaint = VisitComplaint(
            visit_id=data.visit_id,
            raw_complaint_text=data.raw_complaint_text,
            input_mode=data.input_mode,
            language=data.language,
            structured_symptoms=symptoms,
            medical_keywords=keywords,
            icpc_codes=icpc_codes,
            icd_suggestions=[],
            severity_score=max_severity,
            ai_confidence=0.85 if icpc_codes else 0.4,
        )
        self.db.add(complaint)
        await self.db.commit()
        await self.db.refresh(complaint)
        return complaint

    async def get_complaints(self, visit_id: uuid.UUID, org_id: uuid.UUID | None = None) -> list[VisitComplaint]:
        # Check visit ownership
        svc = VisitCreationService(self.db)
        visit = await svc.get_visit(visit_id, org_id=org_id)
        if not visit:
            return []

        r = await self.db.execute(
            select(VisitComplaint).where(VisitComplaint.visit_id == visit_id)
        )
        return list(r.scalars().all())


# ═════════════════════════════════════════════════════════════════════════════
# 3. VISIT CLASSIFICATION SERVICE
# ═════════════════════════════════════════════════════════════════════════════

class ClassificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def classify_visit(self, data: ClassificationCreate, org_id: uuid.UUID | None = None) -> VisitClassification:
        # Check visit ownership
        svc = VisitCreationService(self.db)
        visit_obj = await svc.get_visit(data.visit_id, org_id=org_id)
        if not visit_obj:
            raise ValueError("Visit not found in your organization")

        # Get complaint data
        complaints = await self.db.execute(
            select(VisitComplaint).where(VisitComplaint.visit_id == data.visit_id)
        )
        complaint = complaints.scalar_one_or_none()

        category = ClassificationCategory.routine
        reasons = []
        triggered = []
        complaint_sev = 0.0
        vitals_abnormal = False
        has_chronic = False
        age_risk = False

        # Check complaints
        if complaint:
            complaint_sev = complaint.severity_score or 0
            syms = set(complaint.structured_symptoms or [])

            if syms & EMERGENCY_KEYWORDS:
                category = ClassificationCategory.emergency_opd
                reasons.append(f"Emergency symptoms: {syms & EMERGENCY_KEYWORDS}")
                triggered.append("RULE_EMERGENCY_SYMPTOMS")

            elif syms & PRIORITY_KEYWORDS or complaint_sev >= 6:
                category = ClassificationCategory.priority
                reasons.append(f"Priority symptoms detected (severity={complaint_sev})")
                triggered.append("RULE_PRIORITY_SYMPTOMS")

        # Check vitals
        vitals = data.vitals_snapshot or {}
        if vitals:
            if vitals.get("spo2", 100) < 90:
                category = ClassificationCategory.emergency_opd
                vitals_abnormal = True
                reasons.append(f"SpO2={vitals['spo2']} < 90")
                triggered.append("RULE_LOW_SPO2")
            if vitals.get("bp_sys", 120) > 180:
                category = ClassificationCategory.emergency_opd
                vitals_abnormal = True
                reasons.append(f"BP systolic={vitals['bp_sys']} > 180")
                triggered.append("RULE_HIGH_BP")
            if vitals.get("hr", 80) > 130:
                category = ClassificationCategory.emergency_opd
                vitals_abnormal = True
                reasons.append(f"HR={vitals['hr']} > 130")
                triggered.append("RULE_HIGH_HR")
            if vitals.get("temp", 37) > 39:
                if category == ClassificationCategory.routine:
                    category = ClassificationCategory.priority
                reasons.append(f"Temp={vitals['temp']} > 39")
                triggered.append("RULE_HIGH_TEMP")

        classification = VisitClassification(
            visit_id=data.visit_id,
            category=category,
            classification_reason="; ".join(reasons) if reasons else "No risk factors detected",
            triggered_rules=triggered,
            complaint_severity=complaint_sev,
            vitals_abnormal=vitals_abnormal,
            has_chronic_disease=has_chronic,
            age_risk=age_risk,
            vitals_snapshot=data.vitals_snapshot,
        )
        self.db.add(classification)

        # Update visit priority
        priority_map = {
            ClassificationCategory.emergency_opd: PriorityTag.emergency,
            ClassificationCategory.priority: PriorityTag.priority,
            ClassificationCategory.routine: PriorityTag.normal,
        }
        
        visit_obj.priority_tag = priority_map.get(category, PriorityTag.normal)
        visit_obj.status = VisitStatus.in_queue

        await self.db.commit()
        await self.db.refresh(classification)
        return classification

    async def override_classification(
        self, visit_id: uuid.UUID, override: ClassificationOverride,
        user_id: uuid.UUID, org_id: uuid.UUID | None = None
    ) -> Optional[VisitClassification]:
        # Check visit ownership
        svc = VisitCreationService(self.db)
        visit = await svc.get_visit(visit_id, org_id=org_id)
        if not visit:
            return None

        r = await self.db.execute(
            select(VisitClassification).where(VisitClassification.visit_id == visit_id)
        )
        c = r.scalar_one_or_none()
        if not c:
            return None
        c.category = override.category
        c.is_override = True
        c.override_by = user_id
        c.override_reason = override.override_reason
        await self.db.commit()
        await self.db.refresh(c)
        return c

    async def get_classification(self, visit_id: uuid.UUID, org_id: uuid.UUID | None = None) -> Optional[VisitClassification]:
        # Check visit ownership
        svc = VisitCreationService(self.db)
        visit = await svc.get_visit(visit_id, org_id=org_id)
        if not visit:
            return None

        r = await self.db.execute(
            select(VisitClassification).where(VisitClassification.visit_id == visit_id)
        )
        return r.scalar_one_or_none()


# ═════════════════════════════════════════════════════════════════════════════
# 4. DOCTOR RECOMMENDATION SERVICE
# ═════════════════════════════════════════════════════════════════════════════

class DoctorRecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def recommend_doctor(self, visit_id: uuid.UUID, org_id: uuid.UUID | None = None) -> VisitDoctorRecommendation:
        # Check visit ownership
        svc = VisitCreationService(self.db)
        visit = await svc.get_visit(visit_id, org_id=org_id)
        if not visit:
            raise ValueError("Visit not found in your organization")

        # Get complaints
        complaints = await self.db.execute(
            select(VisitComplaint).where(VisitComplaint.visit_id == visit_id)
        )
        complaint = complaints.scalar_one_or_none()

        recommended_specialty = "General Medicine"
        symptoms = []
        icpc = []

        if complaint:
            symptoms = complaint.structured_symptoms or []
            icpc = complaint.icpc_codes or []

            # Find specialty from symptoms
            for sym in symptoms:
                if sym in SYMPTOM_TO_SPECIALTY:
                    recommended_specialty = SYMPTOM_TO_SPECIALTY[sym]
                    break

        rec = VisitDoctorRecommendation(
            visit_id=visit_id,
            recommended_specialty=recommended_specialty,
            recommended_doctors=[],
            based_on_symptoms=symptoms,
            based_on_icpc=icpc,
            selection_mode="auto",
        )
        self.db.add(rec)
        await self.db.commit()
        await self.db.refresh(rec)
        return rec

    async def select_doctor(
        self, visit_id: uuid.UUID, update: DoctorSelectionUpdate, org_id: uuid.UUID | None = None
    ) -> Optional[VisitDoctorRecommendation]:
        # Check visit ownership
        svc = VisitCreationService(self.db)
        visit_obj = await svc.get_visit(visit_id, org_id=org_id)
        if not visit_obj:
            return None

        r = await self.db.execute(
            select(VisitDoctorRecommendation).where(
                VisitDoctorRecommendation.visit_id == visit_id
            )
        )
        rec = r.scalar_one_or_none()
        if not rec:
            return None
        rec.selected_doctor_id = update.selected_doctor_id
        rec.selection_mode = update.selection_mode
        rec.selected_at = datetime.utcnow()

        # Update visit
        visit_obj.doctor_id = update.selected_doctor_id
        visit_obj.specialty = rec.recommended_specialty

        await self.db.commit()
        await self.db.refresh(rec)
        return rec


# ═════════════════════════════════════════════════════════════════════════════
# 5. QUESTIONNAIRE SERVICE
# ═════════════════════════════════════════════════════════════════════════════

class QuestionnaireService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_template(self, data: QuestionnaireTemplateCreate, org_id: uuid.UUID | None = None) -> VisitQuestionnaireTemplate:
        t = VisitQuestionnaireTemplate(**data.model_dump(), org_id=org_id)
        self.db.add(t)
        await self.db.commit()
        await self.db.refresh(t)
        return t

    async def list_templates(self, specialty: Optional[str] = None, org_id: uuid.UUID | None = None) -> list[VisitQuestionnaireTemplate]:
        q = select(VisitQuestionnaireTemplate).where(VisitQuestionnaireTemplate.is_active == True)
        if org_id:
            q = q.where(VisitQuestionnaireTemplate.org_id == org_id)
        if specialty:
            q = q.where(VisitQuestionnaireTemplate.specialty == specialty)
        r = await self.db.execute(q)
        return list(r.scalars().all())

    async def submit_response(self, data: QuestionnaireResponseCreate, org_id: uuid.UUID | None = None) -> VisitQuestionnaireResponse:
        # Check visit ownership
        svc = VisitCreationService(self.db)
        visit = await svc.get_visit(data.visit_id, org_id=org_id)
        if not visit:
            raise ValueError("Visit not found in your organization")

        resp = VisitQuestionnaireResponse(
            visit_id=data.visit_id,
            template_id=data.template_id,
            patient_id=data.patient_id,
            responses=data.responses,
            completion_source=data.completion_source,
            is_complete=True,
            completed_at=datetime.utcnow(),
        )
        self.db.add(resp)
        await self.db.commit()
        await self.db.refresh(resp)
        return resp

    async def get_responses(self, visit_id: uuid.UUID, org_id: uuid.UUID = None) -> list[VisitQuestionnaireResponse]:
        # Check visit ownership
        svc = VisitCreationService(self.db)
        visit = await svc.get_visit(visit_id, org_id=org_id)
        if not visit:
            return []

        r = await self.db.execute(
            select(VisitQuestionnaireResponse).where(
                VisitQuestionnaireResponse.visit_id == visit_id
            )
        )
        return list(r.scalars().all())


# ═════════════════════════════════════════════════════════════════════════════
# 6. CONTEXT AGGREGATION SERVICE
# ═════════════════════════════════════════════════════════════════════════════

class ContextAggregationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def aggregate_context(self, visit_id: uuid.UUID, org_id: uuid.UUID | None = None) -> VisitContextSnapshot:
        svc = VisitCreationService(self.db)
        visit = await svc.get_visit(visit_id, org_id=org_id)
        if not visit:
            raise ValueError("Visit not found in your organization")

        # Fetch previous visits for this patient
        prev = await self.db.execute(
            select(VisitMaster)
            .where(VisitMaster.patient_id == visit.patient_id)
            .where(VisitMaster.id != visit_id)
            .order_by(VisitMaster.visit_date_time.desc())
            .limit(10)
        )
        past_visits = list(prev.scalars().all())

        # Build context
        diagnoses = []
        prescriptions = []
        last_notes = None
        last_date = None

        for pv in past_visits:
            diagnoses.append({
                "visit_id": str(pv.visit_id),
                "date": pv.visit_date_time.isoformat() if pv.visit_date_time else None,
                "specialty": pv.specialty,
                "department": pv.department,
            })
            if not last_notes:
                last_notes = f"Visit {pv.visit_id} on {pv.visit_date_time.date() if pv.visit_date_time else 'unknown'} — {pv.specialty or 'General'}"
                last_date = pv.visit_date_time

        # Build summary
        summary_parts = []
        if past_visits:
            summary_parts.append(f"Previous visits: {len(past_visits)}")
        if last_date:
            summary_parts.append(f"Last visit: {last_date.date()}")

        snapshot = VisitContextSnapshot(
            visit_id=visit_id,
            patient_id=visit.patient_id,
            previous_diagnoses=diagnoses,
            previous_prescriptions=prescriptions,
            allergies=[],
            chronic_conditions=[],
            last_visit_notes=last_notes,
            last_visit_date=last_date,
            recent_lab_reports=[],
            recent_radiology_reports=[],
            active_medications=[],
            context_summary="; ".join(summary_parts) if summary_parts else "No previous records",
            risk_flags=[],
        )
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def get_context(self, visit_id: uuid.UUID, org_id: uuid.UUID | None = None) -> Optional[VisitContextSnapshot]:
        # Check visit ownership
        svc = VisitCreationService(self.db)
        visit = await svc.get_visit(visit_id, org_id=org_id)
        if not visit:
            return None

        r = await self.db.execute(
            select(VisitContextSnapshot).where(VisitContextSnapshot.visit_id == visit_id)
        )
        return r.scalar_one_or_none()


# ═════════════════════════════════════════════════════════════════════════════
# 7. MULTI-VISIT RULE SERVICE
# ═════════════════════════════════════════════════════════════════════════════

class MultiVisitRuleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_rule(self, data: MultiVisitRuleCreate, org_id: uuid.UUID | None = None) -> MultiVisitRule:
        rule = MultiVisitRule(**data.model_dump(), org_id=org_id)
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def list_rules(self, org_id: uuid.UUID | None = None) -> list[MultiVisitRule]:
        stmt = select(MultiVisitRule).order_by(MultiVisitRule.priority.desc())
        if org_id:
            stmt = stmt.where(MultiVisitRule.org_id == org_id)
        r = await self.db.execute(stmt)
        return list(r.scalars().all())

    async def check_multi_visit(self, visit_id: uuid.UUID, org_id: uuid.UUID | None = None) -> dict:
        svc = VisitCreationService(self.db)
        visit = await svc.get_visit(visit_id, org_id=org_id)
        if not visit:
            return {"action": "none", "reason": "Visit not found in your organization"}

        today = date.today()
        stmt = (
            select(VisitMaster)
            .where(VisitMaster.patient_id == visit.patient_id)
            .where(func.date(VisitMaster.visit_date_time) == today)
            .where(VisitMaster.id != visit_id)
        )
        if org_id:
            stmt = stmt.where(VisitMaster.org_id == org_id)
        
        same_day = await self.db.execute(stmt)
        same_day_visits = list(same_day.scalars().all())

        if not same_day_visits:
            return {"action": "none", "reason": "First visit today"}

        # Check rules
        for sv in same_day_visits:
            if sv.doctor_id == visit.doctor_id:
                return {
                    "action": "mark_follow_up",
                    "reason": f"Same doctor same day — follow-up of {sv.visit_id}",
                    "linked_visit": str(sv.id),
                }
            if sv.specialty != visit.specialty:
                return {
                    "action": "create_new_visit",
                    "reason": f"Different specialty ({sv.specialty} → {visit.specialty})",
                }

        return {"action": "none", "reason": "No rule match"}


# ═════════════════════════════════════════════════════════════════════════════
# 8. VISIT ANALYTICS SERVICE
# ═════════════════════════════════════════════════════════════════════════════

class VisitAnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_daily(self, for_date: str, department: Optional[str] = None, org_id: uuid.UUID | None = None) -> VisitAnalyticsSnapshot:
        d = date.fromisoformat(for_date)
        q = select(VisitMaster).where(func.date(VisitMaster.visit_date_time) == d)
        if org_id:
            q = q.where(VisitMaster.org_id == org_id)
        if department:
            q = q.where(VisitMaster.department == department)
        r = await self.db.execute(q)
        visits = list(r.scalars().all())

        total = len(visits)
        completed = sum(1 for v in visits if v.status == VisitStatus.completed)
        cancelled = sum(1 for v in visits if v.status == VisitStatus.cancelled)
        no_shows = sum(1 for v in visits if v.status == VisitStatus.no_show)
        emergency = sum(1 for v in visits if v.priority_tag == PriorityTag.emergency)
        priority = sum(1 for v in visits if v.priority_tag == PriorityTag.priority)
        routine = total - emergency - priority

        # Top specialties
        spec_count: dict = {}
        complaint_count: dict = {}
        for v in visits:
            if v.specialty:
                spec_count[v.specialty] = spec_count.get(v.specialty, 0) + 1

        top_specs = sorted(spec_count.items(), key=lambda x: x[1], reverse=True)[:5]
        top_specs_list = [{"specialty": s, "count": c} for s, c in top_specs]

        snapshot = VisitAnalyticsSnapshot(
            analytics_date=datetime.combine(d, datetime.min.time()),
            department=department,
            total_visits=total,
            routine_visits=routine,
            priority_visits=priority,
            emergency_visits=emergency,
            completed_visits=completed,
            cancelled_visits=cancelled,
            no_show_visits=no_shows,
            top_specialties=top_specs_list,
            top_complaints=[],
            doctor_load_distribution={},
        )
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def get_dashboard_summary(self, from_date: str, to_date: str, org_id: uuid.UUID | None = None) -> VisitDashboardSummary:
        fd = date.fromisoformat(from_date)
        td = date.fromisoformat(to_date)
        q = select(VisitMaster).where(
            and_(
                func.date(VisitMaster.visit_date_time) >= fd,
                func.date(VisitMaster.visit_date_time) <= td,
            )
        )
        if org_id:
            q = q.where(VisitMaster.org_id == org_id)
        r = await self.db.execute(q)
        visits = list(r.scalars().all())

        total = len(visits)
        completed = sum(1 for v in visits if v.status == VisitStatus.completed)
        cancelled = sum(1 for v in visits if v.status == VisitStatus.cancelled)
        no_shows = sum(1 for v in visits if v.status == VisitStatus.no_show)
        emergency = sum(1 for v in visits if v.priority_tag == PriorityTag.emergency)
        priority = sum(1 for v in visits if v.priority_tag == PriorityTag.priority)
        routine = total - emergency - priority

        spec_count: dict = {}
        for v in visits:
            if v.specialty:
                spec_count[v.specialty] = spec_count.get(v.specialty, 0) + 1
        top_spec = sorted(spec_count.items(), key=lambda x: x[1], reverse=True)[:5]

        return VisitDashboardSummary(
            period_start=from_date,
            period_end=to_date,
            total_visits=total,
            completed=completed,
            cancelled=cancelled,
            no_shows=no_shows,
            emergency_count=emergency,
            priority_count=priority,
            routine_count=routine,
            top_specialties=[{"specialty": s, "count": c} for s, c in top_spec],
            top_complaints=[],
            avg_wait_time_min=None,
        )
