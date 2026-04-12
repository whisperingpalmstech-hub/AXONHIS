"""
AXONHIS AI Platform – Phase 9 Router.

Endpoints:
  POST /ai/summarize-patient          – Generate live patient summary
  GET  /ai/summary/{encounter_id}     – Fetch latest cached summary
  POST /ai/voice-command              – Parse voice transcript
  POST /ai/voice-command/{id}/confirm – Clinician confirms command
  GET  /ai/voice-commands             – Recent voice command log
  GET  /ai/clinical-insights/{enc_id} – Fetch insights for encounter
  POST /ai/clinical-insights/generate – Generate fresh insights
  POST /ai/clinical-insights/{id}/ack – Acknowledge an insight
  GET  /ai/risk-alerts                – Get active risk alerts
  POST /ai/risk-alerts/analyze        – Run risk analysis for encounter
  POST /ai/risk-alerts/{id}/resolve   – Clinician resolves alert
  POST /ai/agents/task                – Create agent draft task
  POST /ai/agents/task/{id}/approve   – Approve agent task
  GET  /ai/agents/tasks               – List agent tasks
"""
import uuid

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import CurrentUser, DBSession
from app.core.ai.schemas import (
    AgentTaskOut,
    AgentTaskRequest,
    ApproveAgentTaskRequest,
    AcknowledgeInsightRequest,
    ClinicalInsightOut,
    ConfirmVoiceCommandRequest,
    PatientSummaryRequest,
    PatientSummaryResponse,
    ResolveAlertRequest,
    RiskAlertOut,
    VoiceCommandRequest,
    VoiceCommandResponse,
)
from app.core.ai.services import (
    AgentOrchestrationService,
    ClinicalInsightService,
    PatientSummaryService,
    RiskDetectionService,
    VoiceProcessingService,
)

router = APIRouter(prefix="/ai", tags=["AI Platform – Phase 9"])


# ─────────────────────────────────────────────────────────────────────────────
# Patient Summary Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/summarize-patient", response_model=PatientSummaryResponse, status_code=201)
async def summarize_patient(
    body: PatientSummaryRequest,
    db: DBSession,
    current_user: CurrentUser,
    force_refresh: bool = Query(default=False, description="Force re-generation even if cached"),
) -> PatientSummaryResponse:
    """
    Generate or retrieve a Grok-powered patient summary for an encounter.
    Summary is cached and marked stale on refresh.
    """
    svc = PatientSummaryService(db)
    summary = await svc.generate_summary(
        encounter_id=body.encounter_id,
        user_id=current_user.id,
        force_refresh=force_refresh,
    )
    return PatientSummaryResponse.model_validate(summary)


@router.get("/summary/{encounter_id}", response_model=PatientSummaryResponse)
async def get_summary(
    encounter_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> PatientSummaryResponse:
    """Fetch the latest cached AI summary for an encounter (generates if none exists)."""
    svc = PatientSummaryService(db)
    summary = await svc.generate_summary(
        encounter_id=encounter_id,
        user_id=current_user.id,
        force_refresh=False,
    )
    return PatientSummaryResponse.model_validate(summary)


# ─────────────────────────────────────────────────────────────────────────────
# Voice Command Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/voice-command", response_model=VoiceCommandResponse, status_code=201)
async def process_voice_command(
    body: VoiceCommandRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> VoiceCommandResponse:
    """
    Parse a voice transcript from the clinician into structured intent.
    Supports EN / HI / MR. Command is NEVER auto-executed — requires confirmation.
    """
    svc = VoiceProcessingService(db)
    cmd = await svc.process_command(
        transcript=body.transcript,
        language=body.language,
        user_id=current_user.id,
        encounter_id=body.encounter_id,
    )
    return VoiceCommandResponse.model_validate(cmd)


@router.post("/voice-command/{command_id}/confirm", response_model=VoiceCommandResponse)
async def confirm_voice_command(
    command_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> VoiceCommandResponse:
    """Clinician confirms a parsed voice command for execution."""
    svc = VoiceProcessingService(db)
    try:
        cmd = await svc.confirm_command(command_id=command_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return VoiceCommandResponse.model_validate(cmd)


@router.get("/voice-commands", response_model=list[VoiceCommandResponse])
async def get_voice_commands(
    db: DBSession,
    current_user: CurrentUser,
    limit: int = Query(default=20, le=100),
) -> list[VoiceCommandResponse]:
    """Retrieve recent voice commands issued by the current user."""
    svc = VoiceProcessingService(db)
    commands = await svc.get_recent_commands(user_id=current_user.id, limit=limit)
    return [VoiceCommandResponse.model_validate(c) for c in commands]


# ─────────────────────────────────────────────────────────────────────────────
# Clinical Insight Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/clinical-insights/generate", response_model=list[ClinicalInsightOut], status_code=201)
async def generate_insights(
    body: PatientSummaryRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> list[ClinicalInsightOut]:
    """
    Run the AI clinical insight engine for an encounter.
    Detects abnormal lab patterns, drug interactions, deterioration signals.
    """
    from sqlalchemy import text

    # Resolve patient_id from encounter
    try:
        result = await db.execute(
            text("SELECT patient_id FROM encounters WHERE id = :eid"),
            {"eid": str(body.encounter_id)},
        )
        row = result.first()
        patient_id = uuid.UUID(str(row[0])) if row else uuid.uuid4()
    except Exception:
        patient_id = uuid.uuid4()

    svc = ClinicalInsightService(db)
    insights = await svc.generate_insights(
        encounter_id=body.encounter_id, patient_id=patient_id
    )
    return [ClinicalInsightOut.model_validate(i) for i in insights]


@router.get("/clinical-insights/{encounter_id}", response_model=list[ClinicalInsightOut])
async def get_clinical_insights(
    encounter_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> list[ClinicalInsightOut]:
    """Fetch all AI insights for a given encounter."""
    svc = ClinicalInsightService(db)
    insights = await svc.get_insights(encounter_id=encounter_id)
    return [ClinicalInsightOut.model_validate(i) for i in insights]


@router.post("/clinical-insights/{insight_id}/acknowledge", response_model=ClinicalInsightOut)
async def acknowledge_insight(
    insight_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> ClinicalInsightOut:
    """Clinician acknowledges a clinical insight."""
    svc = ClinicalInsightService(db)
    ins = await svc.acknowledge(insight_id=insight_id, user_id=current_user.id)
    if not ins:
        raise HTTPException(status_code=404, detail="Insight not found")
    return ClinicalInsightOut.model_validate(ins)


# ─────────────────────────────────────────────────────────────────────────────
# Risk Alert Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/risk-alerts", response_model=list[RiskAlertOut])
async def get_risk_alerts(
    db: DBSession,
    current_user: CurrentUser,
    patient_id: uuid.UUID | None = Query(default=None),
    encounter_id: uuid.UUID | None = Query(default=None),
) -> list[RiskAlertOut]:
    """Fetch all active (unresolved) risk alerts, optionally filtered."""
    svc = RiskDetectionService(db)
    alerts = await svc.get_active_alerts(
        patient_id=patient_id, encounter_id=encounter_id
    )
    return [RiskAlertOut.model_validate(a) for a in alerts]


@router.post("/risk-alerts/analyze", response_model=list[RiskAlertOut], status_code=201)
async def analyze_risk(
    body: PatientSummaryRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> list[RiskAlertOut]:
    """
    Run AI risk analysis for an encounter.
    Detects sepsis risk, drug-allergy conflicts, critical lab abnormalities.
    """
    from sqlalchemy import text

    try:
        result = await db.execute(
            text("SELECT patient_id FROM encounters WHERE id = :eid"),
            {"eid": str(body.encounter_id)},
        )
        row = result.first()
        patient_id = uuid.UUID(str(row[0])) if row else uuid.uuid4()
    except Exception:
        patient_id = uuid.uuid4()

    svc = RiskDetectionService(db)
    alerts = await svc.run_risk_analysis(
        patient_id=patient_id, encounter_id=body.encounter_id
    )
    return [RiskAlertOut.model_validate(a) for a in alerts]


@router.post("/risk-alerts/{alert_id}/resolve", response_model=RiskAlertOut)
async def resolve_alert(
    alert_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> RiskAlertOut:
    """Clinician marks a risk alert as resolved."""
    svc = RiskDetectionService(db)
    alert = await svc.resolve_alert(alert_id=alert_id, user_id=current_user.id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return RiskAlertOut.model_validate(alert)


# ─────────────────────────────────────────────────────────────────────────────
# AI Agent Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/agents/task", response_model=AgentTaskOut, status_code=201)
async def create_agent_task(
    body: AgentTaskRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> AgentTaskOut:
    """
    Start an AI agent task (discharge summary, documentation draft, etc.).
    Generates a DRAFT — clinician must approve before any output is used.
    """
    svc = AgentOrchestrationService(db)
    task = await svc.create_task(
        agent_type=body.agent_type,
        user_id=current_user.id,
        task_input=body.task_input,
        encounter_id=body.encounter_id,
        patient_id=body.patient_id,
    )
    return AgentTaskOut.model_validate(task)


@router.post("/agents/task/{task_id}/approve", response_model=AgentTaskOut)
async def approve_agent_task(
    task_id: uuid.UUID,
    body: ApproveAgentTaskRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> AgentTaskOut:
    """Clinician approves the AI agent draft output."""
    svc = AgentOrchestrationService(db)
    task = await svc.approve_task(task_id=task_id, user_id=current_user.id, draft_output=body.draft_output)
    if not task:
        raise HTTPException(status_code=404, detail="Agent task not found")
    return AgentTaskOut.model_validate(task)


@router.get("/agents/tasks", response_model=list[AgentTaskOut])
async def list_agent_tasks(
    db: DBSession,
    current_user: CurrentUser,
    encounter_id: uuid.UUID | None = Query(default=None),
) -> list[AgentTaskOut]:
    """List AI agent tasks, optionally filtered by encounter."""
    svc = AgentOrchestrationService(db)
    tasks = await svc.get_tasks(
        encounter_id=encounter_id, user_id=current_user.id
    )
    return [AgentTaskOut.model_validate(t) for t in tasks]
