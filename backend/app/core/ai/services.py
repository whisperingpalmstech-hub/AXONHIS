"""
AXONHIS AI Platform – Phase 9 Core Services.

Implements:
  PatientSummaryService   – Grok-powered live patient summary
  VoiceProcessingService  – STT transcript → clinical intent
  ClinicalInsightService  – Detect abnormal patterns & insights
  RiskDetectionService    – Sepsis / drug-allergy / critical lab alerts
  AgentOrchestrationService – Draft-only AI agents (require approval)
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.grok_client import grok_chat, grok_json
from app.core.ai.models import (
    AIAgentTask,
    AgentTaskStatus,
    AISummary,
    ClinicalInsight,
    InsightType,
    RiskAlert,
    AlertCategory,
    AlertSeverity,
    VoiceCommand,
    VoiceCommandStatus,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers – fetch patient data from existing Phase modules
# ─────────────────────────────────────────────────────────────────────────────


async def _fetch_encounter_context(db: AsyncSession, encounter_id: uuid.UUID) -> dict[str, Any]:
    """Aggregate clinical data for an encounter from all Phase tables."""
    from sqlalchemy import text

    context: dict[str, Any] = {}

    # Encounter basic info
    try:
        enc_q = await db.execute(
            text("""
                SELECT e.id, e.patient_id, e.encounter_type, e.status, e.start_time,
                       p.first_name || ' ' || p.last_name AS patient_name,
                       p.date_of_birth, p.gender
                FROM encounters e
                JOIN patients p ON p.id = e.patient_id
                WHERE e.id = :eid
            """),
            {"eid": str(encounter_id)},
        )
        row = enc_q.mappings().first()
        if row:
            context["encounter"] = dict(row)
    except Exception as e:
        logger.warning("Could not fetch encounter: %s", e)
        await db.rollback()
        context["encounter"] = {}

    # Lab results (abnormal first)
    try:
        lab_q = await db.execute(
            text("""
                SELECT lr.value, lr.unit, lr.result_flag, lr.is_critical,
                       lt.name AS test_name, lr.entered_at
                FROM lab_results lr
                JOIN lab_tests lt ON lt.id = lr.test_id
                JOIN lab_orders lo ON lo.id = lr.sample_id
                WHERE lo.encounter_id = :eid
                ORDER BY lr.is_critical DESC, lr.entered_at DESC
                LIMIT 20
            """),
            {"eid": str(encounter_id)},
        )
        context["lab_results"] = [dict(r) for r in lab_q.mappings().all()]
    except Exception as e:
        logger.warning("Could not fetch lab results: %s", e)
        await db.rollback()
        context["lab_results"] = []

    # Active orders (medications / lab / procedures)
    try:
        ord_q = await db.execute(
            text("""
                SELECT o.order_type, o.status, o.notes, o.created_at
                FROM orders o
                WHERE o.encounter_id = :eid
                  AND o.status NOT IN ('CANCELLED', 'COMPLETED')
                ORDER BY o.created_at DESC
                LIMIT 15
            """),
            {"eid": str(encounter_id)},
        )
        context["active_orders"] = [dict(r) for r in ord_q.mappings().all()]
    except Exception as e:
        logger.warning("Could not fetch orders: %s", e)
        await db.rollback()
        context["active_orders"] = []

    # Prescriptions
    try:
        rx_q = await db.execute(
            text("""
                SELECT m.drug_name, pi.dosage as dose, pi.frequency, pr.status
                FROM prescriptions pr
                JOIN prescription_items pi ON pi.prescription_id = pr.id
                JOIN medications m ON m.id = pi.drug_id
                WHERE pr.encounter_id = :eid
                  AND pr.status IN ('pending', 'approved', 'dispensed')
                ORDER BY pr.prescription_time DESC
                LIMIT 10
            """),
            {"eid": str(encounter_id)},
        )
        context["medications"] = [dict(r) for r in rx_q.mappings().all()]
    except Exception as e:
        logger.warning("Could not fetch prescriptions: %s", e)
        await db.rollback()
        context["medications"] = []

    # Diagnoses
    try:
        diag_q = await db.execute(
            text("""
                SELECT d.diagnosis_code, d.diagnosis_description, d.diagnosis_type
                FROM encounter_diagnoses d
                WHERE d.encounter_id = :eid
            """),
            {"eid": str(encounter_id)},
        )
        context["diagnoses"] = [dict(r) for r in diag_q.mappings().all()]
    except Exception as e:
        logger.warning("Could not fetch diagnoses: %s", e)
        await db.rollback()
        context["diagnoses"] = []

    return context


def _build_summary_prompt(ctx: dict[str, Any]) -> list[dict[str, str]]:
    enc = ctx.get("encounter", {})
    labs = ctx.get("lab_results", [])
    meds = ctx.get("medications", [])
    orders = ctx.get("active_orders", [])

    system = (
        "You are a senior clinical AI assistant for a hospital information system. "
        "Generate a concise, structured clinical summary for the treating physician. "
        "Always be medically accurate. Flag critical findings prominently. "
        "Respond ONLY with valid JSON matching the schema provided."
    )

    schema = json.dumps({
        "narrative": "string – 2-3 sentence clinical paragraph",
        "primary_diagnosis": "string or null",
        "active_treatments": ["list of treatment strings"],
        "recent_abnormal_labs": [{"test": "string", "value": "string", "flag": "string"}],
        "pending_tests": ["list of pending test/order strings"],
        "clinical_trends": ["list of clinical trend observations"],
        "risk_flags": ["list of risk flags or empty list"],
    }, indent=2)

    user = f"""
Patient: {enc.get('patient_name', 'Unknown')}
Encounter Type: {enc.get('encounter_type', 'N/A')} | Status: {enc.get('status', 'N/A')}
Chief Complaint: {enc.get('chief_complaint', 'Not recorded')}

Lab Results (most recent):
{json.dumps(labs[:10], default=str) if labs else 'None'}

Active Medications:
{json.dumps(meds, default=str) if meds else 'None'}

Active Orders:
{json.dumps(orders, default=str) if orders else 'None'}

Generate a clinical summary matching this JSON schema:
{schema}
"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Patient Summary Service
# ─────────────────────────────────────────────────────────────────────────────


class PatientSummaryService:
    """
    Generates and caches AI patient summaries using Grok LLM.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def generate_summary(
        self,
        encounter_id: uuid.UUID,
        user_id: uuid.UUID,
        force_refresh: bool = False,
    ) -> AISummary:
        """Generate or return cached summary for an encounter."""
        if not force_refresh:
            cached = await self._get_cached(encounter_id)
            if cached and not cached.is_stale:
                return cached

        ctx = await _fetch_encounter_context(self.db, encounter_id)

        # Attempt Grok with graceful fallback
        try:
            messages = _build_summary_prompt(ctx)
            raw = await grok_json(messages, max_tokens=1500)
        except Exception as e:
            logger.error("Grok summary failed: %s", e)
            raw = {}

        enc = ctx.get("encounter", {})
        patient_id_str = enc.get("patient_id")
        try:
            if patient_id_str:
                patient_id = uuid.UUID(str(patient_id_str))
            else:
                patient_id = uuid.uuid4()
        except Exception:
            patient_id = uuid.uuid4()

        summary = AISummary(
            encounter_id=encounter_id,
            patient_id=patient_id,
            narrative=raw.get("narrative", "Summary could not be generated. Please review patient data manually."),
            primary_diagnosis=raw.get("primary_diagnosis"),
            active_treatments=raw.get("active_treatments", []),
            recent_abnormal_labs=raw.get("recent_abnormal_labs", []),
            pending_tests=raw.get("pending_tests", []),
            clinical_trends=raw.get("clinical_trends", []),
            risk_flags=raw.get("risk_flags", []),
            llm_model="llama-3.3-70b-versatile",
            generated_by=user_id,
        )

        # Mark old summaries as stale
        await self._invalidate_old(encounter_id)
        self.db.add(summary)
        await self.db.commit()
        await self.db.refresh(summary)
        return summary

    async def _get_cached(self, encounter_id: uuid.UUID) -> AISummary | None:
        result = await self.db.execute(
            select(AISummary)
            .where(and_(AISummary.encounter_id == encounter_id, AISummary.is_stale.is_(False)))
            .order_by(desc(AISummary.generated_at))
            .limit(1)
        )
        return result.scalars().first()

    async def _invalidate_old(self, encounter_id: uuid.UUID) -> None:
        from sqlalchemy import update
        try:
            await self.db.execute(
                update(AISummary)
                .where(AISummary.encounter_id == encounter_id)
                .values(is_stale=True)
            )
        except Exception as e:
            logger.warning("Could not invalidate old summaries: %s", e)
            await self.db.rollback()


# ─────────────────────────────────────────────────────────────────────────────
# Voice Processing Service
# ─────────────────────────────────────────────────────────────────────────────

LANG_NAMES = {"en": "English", "hi": "Hindi", "mr": "Marathi"}

VOICE_INTENT_PROMPT_SYSTEM = """
You are a clinical voice command interpreter for a hospital system.
Extract the clinical intent from the clinician's statement and map it to one of:
  create_order | add_note | navigate | query_patient | set_medication | unknown

Respond ONLY with valid JSON:
{
  "intent": "string",
  "confidence": 0.0-1.0,
  "translated_text": "English translation (only if input is not English)",
  "parsed_action": {
    "action_type": "string",
    "parameters": {}
  },
  "suggested_orders": [
    {"order_type": "lab"|"medication"|"procedure", "name": "string", "note": "string"}
  ]
}
"""


class VoiceProcessingService:
    """Process voice transcripts into structured clinical actions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def process_command(
        self,
        transcript: str,
        language: str,
        user_id: uuid.UUID,
        encounter_id: uuid.UUID | None = None,
    ) -> VoiceCommand:
        """Parse transcript and save a VoiceCommand (status=PENDING; never auto-executed)."""
        lang_name = LANG_NAMES.get(language, "English")
        messages = [
            {"role": "system", "content": VOICE_INTENT_PROMPT_SYSTEM},
            {
                "role": "user",
                "content": f"Language: {lang_name}\nClinician said: \"{transcript}\"",
            },
        ]
        try:
            raw = await grok_json(messages, max_tokens=512)
        except Exception as e:
            logger.error("Grok voice parse failed: %s", e)
            raw = {}

        cmd = VoiceCommand(
            issued_by=user_id,
            encounter_id=encounter_id,
            raw_transcript=transcript,
            detected_language=language,
            translated_text=raw.get("translated_text"),
            intent=raw.get("intent", "unknown"),
            parsed_action=raw.get("parsed_action", {}),
            suggested_orders=raw.get("suggested_orders", []),
            confidence=float(raw.get("confidence", 0.0)),
            status=VoiceCommandStatus.PENDING,
        )
        self.db.add(cmd)
        await self.db.commit()
        await self.db.refresh(cmd)
        return cmd

    async def confirm_command(self, command_id: uuid.UUID, user_id: uuid.UUID) -> VoiceCommand:
        """Mark a voice command as confirmed by the clinician (still not executed automatically)."""
        result = await self.db.execute(select(VoiceCommand).where(VoiceCommand.id == command_id))
        cmd = result.scalars().first()
        if cmd is None:
            raise ValueError(f"VoiceCommand {command_id} not found")
        cmd.status = VoiceCommandStatus.CONFIRMED
        cmd.confirmed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(cmd)
        return cmd

    async def get_recent_commands(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> list[VoiceCommand]:
        result = await self.db.execute(
            select(VoiceCommand)
            .where(VoiceCommand.issued_by == user_id)
            .order_by(desc(VoiceCommand.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())


# ─────────────────────────────────────────────────────────────────────────────
# Clinical Insight Service
# ─────────────────────────────────────────────────────────────────────────────

INSIGHT_PROMPT_SYSTEM = """
You are a clinical decision support engine. Analyze patient data and detect clinically relevant insights.
Respond ONLY with a valid JSON array:
[
  {
    "insight_type": "ABNORMAL_LAB|DRUG_INTERACTION|RAPID_DETERIORATION|DELAYED_RESULT|SEPSIS_RISK|GENERAL",
    "title": "short title",
    "description": "detailed clinical explanation",
    "recommendation": "suggested clinical action",
    "confidence_score": 0.0-1.0
  }
]
Return an empty array [] if no significant insights are detected.
"""


class ClinicalInsightService:
    """AI engine for detecting clinically relevant patterns."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def generate_insights(
        self, encounter_id: uuid.UUID, patient_id: uuid.UUID
    ) -> list[ClinicalInsight]:
        ctx = await _fetch_encounter_context(self.db, encounter_id)
        messages = [
            {"role": "system", "content": INSIGHT_PROMPT_SYSTEM},
            {"role": "user", "content": f"Patient clinical data:\n{json.dumps(ctx, default=str)}"},
        ]
        try:
            raw_text = await grok_chat(messages, max_tokens=1024)
            items = json.loads(raw_text["content"])
            if not isinstance(items, list):
                items = []
        except Exception as e:
            logger.error("Grok insight generation failed: %s", e)
            items = []

        insights: list[ClinicalInsight] = []
        for item in items[:10]:  # cap at 10
            insight = ClinicalInsight(
                encounter_id=encounter_id,
                patient_id=patient_id,
                insight_type=item.get("insight_type", InsightType.GENERAL),
                title=item.get("title", "Clinical Insight"),
                description=item.get("description", ""),
                recommendation=item.get("recommendation"),
                confidence_score=float(item.get("confidence_score", 0.5)),
                source_data=json.loads(json.dumps(ctx, default=str)),
            )
            self.db.add(insight)
            insights.append(insight)

        if insights:
            await self.db.commit()
            for ins in insights:
                await self.db.refresh(ins)
        return insights

    async def get_insights(self, encounter_id: uuid.UUID) -> list[ClinicalInsight]:
        result = await self.db.execute(
            select(ClinicalInsight)
            .where(ClinicalInsight.encounter_id == encounter_id)
            .order_by(desc(ClinicalInsight.created_at))
            .limit(50)
        )
        return list(result.scalars().all())

    async def acknowledge(
        self, insight_id: uuid.UUID, user_id: uuid.UUID
    ) -> ClinicalInsight | None:
        result = await self.db.execute(
            select(ClinicalInsight).where(ClinicalInsight.id == insight_id)
        )
        ins = result.scalars().first()
        if ins:
            ins.is_acknowledged = True
            ins.acknowledged_by = user_id
            ins.acknowledged_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(ins)
        return ins


# ─────────────────────────────────────────────────────────────────────────────
# Risk Detection Service
# ─────────────────────────────────────────────────────────────────────────────

RISK_PROMPT_SYSTEM = """
You are a clinical risk detection engine. Analyze patient data and detect risks.
Respond ONLY with a valid JSON array of risk alerts:
[
  {
    "category": "CLINICAL_RISK|MEDICATION_SAFETY|LAB_CRITICAL|PATIENT_DETERIORATION",
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "title": "short alert title",
    "description": "detailed risk description",
    "recommended_action": "immediate clinical action to take"
  }
]
Return [] if no risks are detected. Include sepsis risk, drug-allergy conflicts,
critical lab abnormalities, and deterioration trends when detected.
"""


class RiskDetectionService:
    """Detect clinical risks and create alert records."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def run_risk_analysis(
        self, patient_id: uuid.UUID, encounter_id: uuid.UUID
    ) -> list[RiskAlert]:
        ctx = await _fetch_encounter_context(self.db, encounter_id)

        messages = [
            {"role": "system", "content": RISK_PROMPT_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Analyze clinical risk for this patient:\n"
                    f"{json.dumps(ctx, default=str)}"
                ),
            },
        ]
        try:
            raw_text = await grok_chat(messages, max_tokens=1024)
            items = json.loads(raw_text["content"])
            if not isinstance(items, list):
                items = []
        except Exception as e:
            logger.error("Grok risk analysis failed: %s", e)
            items = []

        alerts: list[RiskAlert] = []
        for item in items[:10]:
            alert = RiskAlert(
                encounter_id=encounter_id,
                patient_id=patient_id,
                category=item.get("category", AlertCategory.CLINICAL_RISK),
                severity=item.get("severity", AlertSeverity.MEDIUM),
                title=item.get("title", "Risk Alert"),
                description=item.get("description", ""),
                recommended_action=item.get("recommended_action"),
                source_data=json.loads(json.dumps(ctx, default=str)),
            )
            self.db.add(alert)
            alerts.append(alert)

        if alerts:
            await self.db.commit()
            for a in alerts:
                await self.db.refresh(a)
        return alerts

    async def get_active_alerts(
        self, patient_id: uuid.UUID | None = None, encounter_id: uuid.UUID | None = None
    ) -> list[RiskAlert]:
        conditions = [RiskAlert.is_resolved.is_(False)]
        if patient_id:
            conditions.append(RiskAlert.patient_id == patient_id)
        if encounter_id:
            conditions.append(RiskAlert.encounter_id == encounter_id)
        result = await self.db.execute(
            select(RiskAlert)
            .where(and_(*conditions))
            .order_by(desc(RiskAlert.created_at))
            .limit(50)
        )
        return list(result.scalars().all())

    async def resolve_alert(
        self, alert_id: uuid.UUID, user_id: uuid.UUID
    ) -> RiskAlert | None:
        result = await self.db.execute(select(RiskAlert).where(RiskAlert.id == alert_id))
        alert = result.scalars().first()
        if alert:
            alert.is_resolved = True
            alert.resolved_by = user_id
            alert.resolved_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(alert)
        return alert


# ─────────────────────────────────────────────────────────────────────────────
# AI Agent Orchestration Service
# ─────────────────────────────────────────────────────────────────────────────

AGENT_PROMPTS = {
    "discharge_summary": """
You are a clinical documentation assistant. Draft a patient discharge summary.
Include: diagnosis, treatment given, medications on discharge, follow-up instructions.
Respond as a well-formatted clinical document string.
""",
    "documentation_draft": """
You are a clinical documentation assistant. Draft a clinical note based on encounter data.
Include SOAP format (Subjective, Objective, Assessment, Plan).
""",
    "clinical_data_summary": """
Summarize the patient's clinical data into a brief report for handoff.
Include: active problems, medications, recent labs, and next steps.
""",
    "workflow_reminder": """
Generate workflow reminders for the clinical team based on patient status.
List pending actions, overdue tasks, and follow-up items as a bullet list.
""",
}


class AgentOrchestrationService:
    """
    AI agent coordinator. Generates DRAFT outputs only.
    All output MUST be reviewed and approved by a clinician before any action.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_task(
        self,
        agent_type: str,
        user_id: uuid.UUID,
        task_input: dict[str, Any],
        encounter_id: uuid.UUID | None = None,
        patient_id: uuid.UUID | None = None,
    ) -> AIAgentTask:
        task = AIAgentTask(
            agent_type=agent_type,
            encounter_id=encounter_id,
            patient_id=patient_id,
            requested_by=user_id,
            task_input=task_input,
            status=AgentTaskStatus.RUNNING,
        )

        # Generate draft
        try:
            system_prompt = AGENT_PROMPTS.get(
                agent_type,
                "You are a clinical AI assistant. Respond helpfully based on context."
            )
            ctx: dict[str, Any] = task_input.copy()
            if encounter_id:
                enc_ctx = await _fetch_encounter_context(self.db, encounter_id)
                ctx.update(enc_ctx)

            messages = [
                {"role": "system", "content": system_prompt.strip()},
                {
                    "role": "user",
                    "content": f"Patient context:\n{json.dumps(ctx, default=str)}\n\nGenerate the draft:",
                },
            ]
            resp = await grok_chat(messages, max_tokens=2000, temperature=0.4)
            task.draft_output = resp["content"]
            task.status = AgentTaskStatus.AWAITING_APPROVAL
            task.task_input = json.loads(json.dumps(task_input, default=str))
        except Exception as e:
            logger.error("Agent task failed: %s", e)
            task.status = AgentTaskStatus.FAILED
            task.error_message = str(e)

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def approve_task(
        self, task_id: uuid.UUID, user_id: uuid.UUID, draft_output: str | None = None
    ) -> AIAgentTask | None:
        result = await self.db.execute(select(AIAgentTask).where(AIAgentTask.id == task_id))
        task = result.scalars().first()
        if task:
            if draft_output is not None:
                task.draft_output = draft_output
            task.status = AgentTaskStatus.APPROVED
            task.approved_by = user_id
            task.approved_at = datetime.now(timezone.utc)
            task.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(task)
        return task

    async def get_tasks(
        self, encounter_id: uuid.UUID | None = None, user_id: uuid.UUID | None = None
    ) -> list[AIAgentTask]:
        conditions = []
        if encounter_id:
            conditions.append(AIAgentTask.encounter_id == encounter_id)
        if user_id:
            conditions.append(AIAgentTask.requested_by == user_id)
        q = select(AIAgentTask).order_by(desc(AIAgentTask.created_at)).limit(50)
        if conditions:
            q = q.where(and_(*conditions))
        result = await self.db.execute(q)
        return list(result.scalars().all())
