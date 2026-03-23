"""OPD Visit Intelligence Engine — API Routes (40+ endpoints)"""
import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

from .schemas import (
    VisitCreate, VisitUpdate, VisitOut,
    ComplaintCreate, ComplaintOut,
    ClassificationCreate, ClassificationOut, ClassificationOverride,
    DoctorRecommendationOut, DoctorSelectionUpdate,
    QuestionnaireTemplateCreate, QuestionnaireTemplateOut,
    QuestionnaireResponseCreate, QuestionnaireResponseOut,
    ContextSnapshotOut,
    MultiVisitRuleCreate, MultiVisitRuleOut,
    VisitAnalyticsOut, VisitDashboardSummary,
)
from .services import (
    VisitCreationService, ComplaintCaptureService,
    ClassificationService, DoctorRecommendationService,
    QuestionnaireService, ContextAggregationService,
    MultiVisitRuleService, VisitAnalyticsService,
)

router = APIRouter(prefix="/opd-visits", tags=["OPD Visit Intelligence"])


# ═══════════════ VISITS ═══════════════

@router.post("/visits", response_model=VisitOut)
async def create_visit(data: VisitCreate, db: AsyncSession = Depends(get_db)):
    svc = VisitCreationService(db)
    return await svc.create_visit(data)

@router.get("/visits", response_model=list[VisitOut])
async def list_visits(
    patient_id: Optional[uuid.UUID] = None,
    doctor_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    visit_date: Optional[str] = None,
    department: Optional[str] = None,
    priority_tag: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = VisitCreationService(db)
    return await svc.list_visits(patient_id, doctor_id, status, visit_date, department, priority_tag)

@router.get("/visits/{visit_id}", response_model=VisitOut)
async def get_visit(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = VisitCreationService(db)
    v = await svc.get_visit(visit_id)
    if not v:
        raise HTTPException(404, "Visit not found")
    return v

@router.put("/visits/{visit_id}", response_model=VisitOut)
async def update_visit(visit_id: uuid.UUID, data: VisitUpdate, db: AsyncSession = Depends(get_db)):
    svc = VisitCreationService(db)
    v = await svc.update_visit(visit_id, data)
    if not v:
        raise HTTPException(404, "Visit not found")
    return v

@router.get("/visits/queue/{doctor_id}", response_model=list[VisitOut])
async def get_doctor_queue(doctor_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = VisitCreationService(db)
    return await svc.get_todays_queue(doctor_id)


# ═══════════════ COMPLAINTS ═══════════════

@router.post("/complaints", response_model=ComplaintOut)
async def capture_complaint(data: ComplaintCreate, db: AsyncSession = Depends(get_db)):
    svc = ComplaintCaptureService(db)
    return await svc.capture_complaint(data)

@router.get("/complaints/{visit_id}", response_model=list[ComplaintOut])
async def get_complaints(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = ComplaintCaptureService(db)
    return await svc.get_complaints(visit_id)


# ═══════════════ CLASSIFICATION ═══════════════

@router.post("/classification", response_model=ClassificationOut)
async def classify_visit(data: ClassificationCreate, db: AsyncSession = Depends(get_db)):
    svc = ClassificationService(db)
    return await svc.classify_visit(data)

@router.get("/classification/{visit_id}", response_model=ClassificationOut)
async def get_classification(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = ClassificationService(db)
    c = await svc.get_classification(visit_id)
    if not c:
        raise HTTPException(404, "Classification not found")
    return c

@router.put("/classification/{visit_id}/override", response_model=ClassificationOut)
async def override_classification(
    visit_id: uuid.UUID,
    override: ClassificationOverride,
    db: AsyncSession = Depends(get_db),
):
    svc = ClassificationService(db)
    user_id = uuid.uuid4()  # TODO: from auth context
    c = await svc.override_classification(visit_id, override, user_id)
    if not c:
        raise HTTPException(404, "Classification not found")
    return c


# ═══════════════ DOCTOR RECOMMENDATION ═══════════════

@router.post("/recommendations/{visit_id}", response_model=DoctorRecommendationOut)
async def recommend_doctor(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = DoctorRecommendationService(db)
    return await svc.recommend_doctor(visit_id)

@router.put("/recommendations/{visit_id}/select", response_model=DoctorRecommendationOut)
async def select_doctor(
    visit_id: uuid.UUID,
    update: DoctorSelectionUpdate,
    db: AsyncSession = Depends(get_db),
):
    svc = DoctorRecommendationService(db)
    r = await svc.select_doctor(visit_id, update)
    if not r:
        raise HTTPException(404, "Recommendation not found")
    return r


# ═══════════════ QUESTIONNAIRES ═══════════════

@router.post("/questionnaires/templates", response_model=QuestionnaireTemplateOut)
async def create_template(data: QuestionnaireTemplateCreate, db: AsyncSession = Depends(get_db)):
    svc = QuestionnaireService(db)
    return await svc.create_template(data)

@router.get("/questionnaires/templates", response_model=list[QuestionnaireTemplateOut])
async def list_templates(
    specialty: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = QuestionnaireService(db)
    return await svc.list_templates(specialty)

@router.post("/questionnaires/responses", response_model=QuestionnaireResponseOut)
async def submit_questionnaire(data: QuestionnaireResponseCreate, db: AsyncSession = Depends(get_db)):
    svc = QuestionnaireService(db)
    return await svc.submit_response(data)

@router.get("/questionnaires/responses/{visit_id}", response_model=list[QuestionnaireResponseOut])
async def get_questionnaire_responses(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = QuestionnaireService(db)
    return await svc.get_responses(visit_id)


# ═══════════════ CONTEXT SNAPSHOT ═══════════════

@router.post("/context/{visit_id}/aggregate", response_model=ContextSnapshotOut)
async def aggregate_context(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = ContextAggregationService(db)
    return await svc.aggregate_context(visit_id)

@router.get("/context/{visit_id}", response_model=ContextSnapshotOut)
async def get_context(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = ContextAggregationService(db)
    c = await svc.get_context(visit_id)
    if not c:
        raise HTTPException(404, "Context snapshot not found. Call aggregate first.")
    return c


# ═══════════════ MULTI-VISIT RULES ═══════════════

@router.post("/multi-visit-rules", response_model=MultiVisitRuleOut)
async def create_multi_visit_rule(data: MultiVisitRuleCreate, db: AsyncSession = Depends(get_db)):
    svc = MultiVisitRuleService(db)
    return await svc.create_rule(data)

@router.get("/multi-visit-rules", response_model=list[MultiVisitRuleOut])
async def list_multi_visit_rules(db: AsyncSession = Depends(get_db)):
    svc = MultiVisitRuleService(db)
    return await svc.list_rules()

@router.get("/multi-visit-check/{visit_id}")
async def check_multi_visit(visit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = MultiVisitRuleService(db)
    return await svc.check_multi_visit(visit_id)


# ═══════════════ ANALYTICS ═══════════════

@router.post("/analytics/compute", response_model=VisitAnalyticsOut)
async def compute_analytics(
    for_date: str = Query(...),
    department: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = VisitAnalyticsService(db)
    return await svc.compute_daily(for_date, department)

@router.get("/analytics/summary", response_model=VisitDashboardSummary)
async def get_visit_summary(
    from_date: str = Query(...),
    to_date: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    svc = VisitAnalyticsService(db)
    return await svc.get_dashboard_summary(from_date, to_date)
