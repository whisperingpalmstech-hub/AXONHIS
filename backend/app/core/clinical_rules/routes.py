from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clinical_rules.schemas import (
    ClinicalRuleCreate,
    ClinicalRuleUpdate,
    ClinicalRuleResponse,
    RuleExecutionCreate,
    RuleExecutionResponse,
    RuleAlertResponse,
    RuleEvaluationContext,
    RuleEvaluationResult,
    RuleSearchQuery,
    RuleSearchResponse
)
from app.core.clinical_rules.services import ClinicalRuleEngine
from app.database import get_db

router = APIRouter(prefix="/clinical-rules", tags=["clinical-rules"])


@router.post("/rules", response_model=ClinicalRuleResponse)
async def create_rule(
    rule_data: ClinicalRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new clinical rule."""
    engine = ClinicalRuleEngine(db)
    rule = await engine.create_rule(rule_data)
    return rule


@router.put("/rules/{rule_id}", response_model=ClinicalRuleResponse)
async def update_rule(
    rule_id: UUID,
    update_data: ClinicalRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing clinical rule."""
    engine = ClinicalRuleEngine(db)
    rule = await engine.update_rule(rule_id, update_data)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.get("/rules/{rule_id}", response_model=ClinicalRuleResponse)
async def get_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific clinical rule."""
    engine = ClinicalRuleEngine(db)
    rule = await engine.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/rules/search", response_model=RuleSearchResponse)
async def search_rules(
    query: RuleSearchQuery,
    db: AsyncSession = Depends(get_db)
):
    """Search clinical rules with filters."""
    engine = ClinicalRuleEngine(db)
    rules, total_count = await engine.search_rules(query)
    has_more = (query.offset + query.limit) < total_count
    return RuleSearchResponse(
        rules=rules,
        total_count=total_count,
        has_more=has_more
    )


@router.post("/rules/{rule_id}/execute")
async def execute_rule(
    rule_id: UUID,
    context: RuleEvaluationContext,
    db: AsyncSession = Depends(get_db)
):
    """Execute a specific rule."""
    engine = ClinicalRuleEngine(db)
    result = await engine.execute_rule(rule_id, context)
    return result


@router.post("/rules/evaluate-trigger")
async def evaluate_rules_for_trigger(
    trigger_type: str,
    context: RuleEvaluationContext,
    db: AsyncSession = Depends(get_db)
):
    """Evaluate all active rules for a given trigger type."""
    engine = ClinicalRuleEngine(db)
    results = await engine.evaluate_rules_for_trigger(trigger_type, context)
    return results


@router.get("/patients/{patient_id}/alerts", response_model=List[RuleAlertResponse])
async def get_patient_alerts(
    patient_id: UUID,
    encounter_id: UUID = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Get alerts for a patient."""
    engine = ClinicalRuleEngine(db)
    alerts = await engine.get_patient_alerts(patient_id, encounter_id, active_only)
    return alerts


@router.put("/alerts/{alert_id}/acknowledge", response_model=RuleAlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    acknowledged_by: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an alert."""
    engine = ClinicalRuleEngine(db)
    alert = await engine.acknowledge_alert(alert_id, acknowledged_by)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.put("/alerts/{alert_id}/dismiss", response_model=RuleAlertResponse)
async def dismiss_alert(
    alert_id: UUID,
    dismissed_by: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Dismiss an alert."""
    engine = ClinicalRuleEngine(db)
    alert = await engine.dismiss_alert(alert_id, dismissed_by)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
