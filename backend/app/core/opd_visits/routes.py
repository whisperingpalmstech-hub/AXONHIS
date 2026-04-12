"""OPD Visit Intelligence Engine — API Routes (40+ endpoints)"""
import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import CurrentUser

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
async def create_visit(data: VisitCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = VisitCreationService(db)
    return await svc.create_visit(data, org_id=user.org_id)

@router.get("/visits", response_model=list[VisitOut])
async def list_visits(
    user: CurrentUser,
    patient_id: Optional[uuid.UUID] = None,
    doctor_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    visit_date: Optional[str] = None,
    department: Optional[str] = None,
    priority_tag: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = VisitCreationService(db)
    return await svc.list_visits(patient_id, doctor_id, status, visit_date, department, priority_tag, org_id=user.org_id)

@router.get("/visits/{visit_id}", response_model=VisitOut)
async def get_visit(visit_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = VisitCreationService(db)
    v = await svc.get_visit(visit_id, org_id=user.org_id)
    if not v:
        raise HTTPException(404, "Visit not found in your organization")
    return v

@router.put("/visits/{visit_id}", response_model=VisitOut)
async def update_visit(visit_id: uuid.UUID, data: VisitUpdate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = VisitCreationService(db)
    v = await svc.update_visit(visit_id, data, org_id=user.org_id)
    if not v:
        raise HTTPException(404, "Visit not found in your organization")
    return v

@router.get("/visits/queue/{doctor_id}", response_model=list[VisitOut])
async def get_doctor_queue(doctor_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = VisitCreationService(db)
    return await svc.get_todays_queue(doctor_id, org_id=user.org_id)


# ═══════════════ COMPLAINTS ═══════════════

@router.post("/complaints", response_model=ComplaintOut)
async def capture_complaint(data: ComplaintCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = ComplaintCaptureService(db)
    return await svc.capture_complaint(data, org_id=user.org_id)

@router.get("/complaints/{visit_id}", response_model=list[ComplaintOut])
async def get_complaints(visit_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = ComplaintCaptureService(db)
    return await svc.get_complaints(visit_id, org_id=user.org_id)


# ═══════════════ CLASSIFICATION ═══════════════

@router.post("/classification", response_model=ClassificationOut)
async def classify_visit(data: ClassificationCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = ClassificationService(db)
    return await svc.classify_visit(data, org_id=user.org_id)

@router.get("/classification/{visit_id}", response_model=ClassificationOut)
async def get_classification(visit_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = ClassificationService(db)
    c = await svc.get_classification(visit_id, org_id=user.org_id)
    if not c:
        raise HTTPException(404, "Classification not found")
    return c

@router.put("/classification/{visit_id}/override", response_model=ClassificationOut)
async def override_classification(
    visit_id: uuid.UUID,
    override: ClassificationOverride,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    svc = ClassificationService(db)
    c = await svc.override_classification(visit_id, override, user.id, org_id=user.org_id)
    if not c:
        raise HTTPException(404, "Classification not found")
    return c


# ═══════════════ DOCTOR RECOMMENDATION ═══════════════

@router.post("/recommendations/{visit_id}", response_model=DoctorRecommendationOut)
async def recommend_doctor(visit_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = DoctorRecommendationService(db)
    return await svc.recommend_doctor(visit_id, org_id=user.org_id)

@router.put("/recommendations/{visit_id}/select", response_model=DoctorRecommendationOut)
async def select_doctor(
    visit_id: uuid.UUID,
    update: DoctorSelectionUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    svc = DoctorRecommendationService(db)
    r = await svc.select_doctor(visit_id, update, org_id=user.org_id)
    if not r:
        raise HTTPException(404, "Recommendation not found")
    return r


# ═══════════════ QUESTIONNAIRES ═══════════════

@router.post("/questionnaires/templates", response_model=QuestionnaireTemplateOut)
async def create_template(data: QuestionnaireTemplateCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = QuestionnaireService(db)
    return await svc.create_template(data, org_id=user.org_id)

@router.get("/questionnaires/templates", response_model=list[QuestionnaireTemplateOut])
async def list_templates(
    user: CurrentUser,
    specialty: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = QuestionnaireService(db)
    return await svc.list_templates(specialty, org_id=user.org_id)

@router.post("/questionnaires/responses", response_model=QuestionnaireResponseOut)
async def submit_questionnaire(data: QuestionnaireResponseCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = QuestionnaireService(db)
    return await svc.submit_response(data, org_id=user.org_id)

@router.get("/questionnaires/responses/{visit_id}", response_model=list[QuestionnaireResponseOut])
async def get_questionnaire_responses(visit_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = QuestionnaireService(db)
    return await svc.get_responses(visit_id, org_id=user.org_id)


# ═══════════════ CONTEXT SNAPSHOT ═══════════════

@router.post("/context/{visit_id}/aggregate", response_model=ContextSnapshotOut)
async def aggregate_context(visit_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = ContextAggregationService(db)
    return await svc.aggregate_context(visit_id, org_id=user.org_id)

@router.get("/context/{visit_id}", response_model=ContextSnapshotOut)
async def get_context(visit_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = ContextAggregationService(db)
    c = await svc.get_context(visit_id, org_id=user.org_id)
    if not c:
        raise HTTPException(404, "Context snapshot not found. Call aggregate first.")
    return c


# ═══════════════ MULTI-VISIT RULES ═══════════════

@router.post("/multi-visit-rules", response_model=MultiVisitRuleOut)
async def create_multi_visit_rule(data: MultiVisitRuleCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = MultiVisitRuleService(db)
    return await svc.create_rule(data, org_id=user.org_id)

@router.get("/multi-visit-rules", response_model=list[MultiVisitRuleOut])
async def list_multi_visit_rules(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = MultiVisitRuleService(db)
    return await svc.list_rules(org_id=user.org_id)

@router.get("/multi-visit-check/{visit_id}")
async def check_multi_visit(visit_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = MultiVisitRuleService(db)
    return await svc.check_multi_visit(visit_id, org_id=user.org_id)


# ═══════════════ ANALYTICS ═══════════════

@router.post("/analytics/compute", response_model=VisitAnalyticsOut)
async def compute_analytics(
    user: CurrentUser,
    for_date: str = Query(...),
    department: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = VisitAnalyticsService(db)
    return await svc.compute_daily(for_date, department, org_id=user.org_id)

@router.get("/analytics/summary", response_model=VisitDashboardSummary)
async def get_visit_summary(
    user: CurrentUser,
    from_date: str = Query(...),
    to_date: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    svc = VisitAnalyticsService(db)
    return await svc.get_dashboard_summary(from_date, to_date, org_id=user.org_id)
