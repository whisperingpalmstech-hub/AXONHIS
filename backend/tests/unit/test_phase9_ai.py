"""
Phase 9 – AI Platform unit tests.

Tests validate:
  - PatientSummaryService (mocked Grok)
  - VoiceProcessingService (mocked Grok)
  - ClinicalInsightService (mocked Grok)
  - RiskDetectionService (mocked Grok)
  - AgentOrchestrationService (mocked Grok)

All tests mock Grok calls so they run without an internet connection.
"""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.models import (
    AIAgentTask,
    AgentTaskStatus,
    AISummary,
    ClinicalInsight,
    RiskAlert,
    VoiceCommand,
    VoiceCommandStatus,
)
from app.core.ai.services import (
    AgentOrchestrationService,
    ClinicalInsightService,
    PatientSummaryService,
    RiskDetectionService,
    VoiceProcessingService,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

MOCK_ENCOUNTER_CTX = {
    "encounter": {
        "id": str(uuid.uuid4()),
        "patient_id": str(uuid.uuid4()),
        "patient_name": "John Doe",
        "encounter_type": "IPD",
        "status": "ACTIVE",
        "chief_complaint": "Fever and cough",
    },
    "lab_results": [
        {"test_name": "CRP", "value": "45.2", "unit": "mg/L", "result_flag": "HIGH", "is_critical": False}
    ],
    "medications": [
        {"drug_name": "Amoxicillin", "dose": "500mg", "route": "oral", "frequency": "TID", "status": "dispensed"}
    ],
    "active_orders": [],
}

MOCK_SUMMARY_JSON = {
    "narrative": "65-year-old male admitted for pneumonia. Receiving antibiotics. CRP elevated.",
    "primary_diagnosis": "Community-acquired pneumonia",
    "active_treatments": ["IV Amoxicillin 500mg TID"],
    "recent_abnormal_labs": [{"test": "CRP", "value": "45.2 mg/L", "flag": "HIGH"}],
    "pending_tests": ["Culture and sensitivity"],
    "clinical_trends": ["Improving fever trend"],
    "risk_flags": [],
}

MOCK_INSIGHTS_JSON = [
    {
        "insight_type": "ABNORMAL_LAB",
        "title": "Elevated CRP",
        "description": "CRP is markedly elevated at 45.2 mg/L, indicating active inflammation.",
        "recommendation": "Consider repeating CRP in 48 hours to monitor treatment response.",
        "confidence_score": 0.9,
    }
]

MOCK_RISK_JSON = [
    {
        "category": "CLINICAL_RISK",
        "severity": "MEDIUM",
        "title": "Sepsis Screening Recommended",
        "description": "Patient has elevated inflammatory markers with fever.",
        "recommended_action": "Perform qSOFA assessment; consider blood cultures.",
    }
]

MOCK_AGENT_DRAFT = "DISCHARGE SUMMARY\nDiagnosis: Community-acquired pneumonia\nTreatment: Amoxicillin 500mg TID x7 days\nFollow-up: In 1 week."


# ── Patient Summary Tests ─────────────────────────────────────────────────────


class TestPatientSummaryService:
    @pytest.mark.asyncio
    async def test_generate_summary_success(self, db: AsyncSession, doctor_user, test_encounter):
        """Should generate and persist an AI summary using Grok."""
        encounter_id = test_encounter.id
        ctx = MOCK_ENCOUNTER_CTX.copy()
        ctx["encounter"] = ctx["encounter"].copy()
        ctx["encounter"]["patient_id"] = str(test_encounter.patient_id) # type: ignore
        ctx["encounter"]["id"] = str(test_encounter.id) # type: ignore

        with (
            patch(
                "app.core.ai.services._fetch_encounter_context",
                new=AsyncMock(return_value=ctx),
            ),
            patch(
                "app.core.ai.services.grok_json",
                new=AsyncMock(return_value=MOCK_SUMMARY_JSON),
            ),
        ):
            svc = PatientSummaryService(db)
            summary = await svc.generate_summary(
                encounter_id=encounter_id,
                user_id=doctor_user.id,
            )

        assert isinstance(summary, AISummary)
        assert "pneumonia" in summary.narrative.lower()
        assert summary.primary_diagnosis == "Community-acquired pneumonia"
        assert len(summary.active_treatments) == 1
        assert not summary.is_stale

    @pytest.mark.asyncio
    async def test_generate_summary_grok_failure_fallback(self, db: AsyncSession, doctor_user, test_encounter):
        """When Grok fails, should still return a summary with fallback text."""
        encounter_id = test_encounter.id
        ctx = MOCK_ENCOUNTER_CTX.copy()
        ctx["encounter"] = ctx["encounter"].copy()
        ctx["encounter"]["patient_id"] = str(test_encounter.patient_id) # type: ignore
        ctx["encounter"]["id"] = str(test_encounter.id) # type: ignore

        with (
            patch(
                "app.core.ai.services._fetch_encounter_context",
                new=AsyncMock(return_value=ctx),
            ),
            patch(
                "app.core.ai.services.grok_json",
                new=AsyncMock(side_effect=Exception("Grok timeout")),
            ),
        ):
            svc = PatientSummaryService(db)
            summary = await svc.generate_summary(
                encounter_id=encounter_id,
                user_id=doctor_user.id,
            )

        assert isinstance(summary, AISummary)
        assert "manually" in summary.narrative.lower()
        assert summary.narrative  # not empty

    @pytest.mark.asyncio
    async def test_cached_summary_returned(self, db: AsyncSession, doctor_user, test_encounter):
        """Second call without force_refresh should return cached summary."""
        encounter_id = test_encounter.id
        ctx = MOCK_ENCOUNTER_CTX.copy()
        ctx["encounter"] = ctx["encounter"].copy()
        ctx["encounter"]["patient_id"] = str(test_encounter.patient_id) # type: ignore
        ctx["encounter"]["id"] = str(test_encounter.id) # type: ignore

        with (
            patch(
                "app.core.ai.services._fetch_encounter_context",
                new=AsyncMock(return_value=ctx),
            ),
            patch(
                "app.core.ai.services.grok_json",
                new=AsyncMock(return_value=MOCK_SUMMARY_JSON),
            ) as mock_grok,
        ):
            svc = PatientSummaryService(db)
            s1 = await svc.generate_summary(encounter_id=encounter_id, user_id=doctor_user.id)
            s2 = await svc.generate_summary(encounter_id=encounter_id, user_id=doctor_user.id)

        # Grok called once only (second call hits cache)
        assert mock_grok.call_count == 1
        assert s1.id == s2.id


# ── Voice Processing Tests ────────────────────────────────────────────────────


class TestVoiceProcessingService:
    @pytest.mark.asyncio
    async def test_parse_english_command(self, db: AsyncSession, doctor_user):
        """Should parse English voice command and return structured intent."""
        grok_response = {
            "intent": "create_order",
            "confidence": 0.95,
            "translated_text": None,
            "parsed_action": {"action_type": "lab_order", "parameters": {"tests": ["CBC", "CRP"]}},
            "suggested_orders": [
                {"order_type": "lab", "name": "CBC", "note": "Complete blood count"},
                {"order_type": "lab", "name": "CRP", "note": "C-reactive protein"},
            ],
        }
        with patch("app.core.ai.services.grok_json", new=AsyncMock(return_value=grok_response)):
            svc = VoiceProcessingService(db)
            cmd = await svc.process_command(
                transcript="Order CBC and CRP",
                language="en",
                user_id=doctor_user.id,
            )

        assert isinstance(cmd, VoiceCommand)
        assert cmd.intent == "create_order"
        assert cmd.confidence == 0.95
        assert len(cmd.suggested_orders) == 2
        assert cmd.status == VoiceCommandStatus.PENDING

    @pytest.mark.asyncio
    async def test_parse_hindi_command(self, db: AsyncSession, doctor_user):
        """Should handle Hindi input with translation."""
        grok_response = {
            "intent": "create_order",
            "confidence": 0.88,
            "translated_text": "Order complete blood count",
            "parsed_action": {"action_type": "lab_order", "parameters": {"tests": ["CBC"]}},
            "suggested_orders": [{"order_type": "lab", "name": "CBC", "note": ""}],
        }
        with patch("app.core.ai.services.grok_json", new=AsyncMock(return_value=grok_response)):
            svc = VoiceProcessingService(db)
            cmd = await svc.process_command(
                transcript="CBC टेस्ट करो",
                language="hi",
                user_id=doctor_user.id,
            )

        assert cmd.detected_language == "hi"
        assert cmd.translated_text is not None
        assert cmd.status == VoiceCommandStatus.PENDING  # NOT auto-executed

    @pytest.mark.asyncio
    async def test_confirm_command(self, db: AsyncSession, doctor_user):
        """Doctor should be able to confirm a pending voice command."""
        grok_response = {
            "intent": "create_order",
            "confidence": 0.9,
            "translated_text": None,
            "parsed_action": {},
            "suggested_orders": [],
        }
        with patch("app.core.ai.services.grok_json", new=AsyncMock(return_value=grok_response)):
            svc = VoiceProcessingService(db)
            cmd = await svc.process_command("Order CBC", "en", doctor_user.id)

        confirmed = await svc.confirm_command(cmd.id, doctor_user.id)
        assert confirmed.status == VoiceCommandStatus.CONFIRMED
        assert confirmed.confirmed_at is not None

    @pytest.mark.asyncio
    async def test_confirm_nonexistent_command_raises(self, db: AsyncSession, doctor_user):
        """Confirming a missing command should raise ValueError."""
        svc = VoiceProcessingService(db)
        with pytest.raises(ValueError, match="not found"):
            await svc.confirm_command(uuid.uuid4(), doctor_user.id)


# ── Clinical Insight Tests ────────────────────────────────────────────────────


class TestClinicalInsightService:
    @pytest.mark.asyncio
    async def test_generate_insights(self, db: AsyncSession, test_patient, test_encounter):
        """Should generate and persist clinical insights."""
        encounter_id = test_encounter.id
        patient_id = test_patient.id

        with (
            patch(
                "app.core.ai.services._fetch_encounter_context",
                new=AsyncMock(return_value=MOCK_ENCOUNTER_CTX),
            ),
            patch(
                "app.core.ai.services.grok_chat",
                new=AsyncMock(return_value={"content": str(MOCK_INSIGHTS_JSON).replace("'", '"')}),
            ),
        ):
            svc = ClinicalInsightService(db)
            insights = await svc.generate_insights(
                encounter_id=encounter_id, patient_id=patient_id
            )

        assert len(insights) > 0
        assert isinstance(insights[0], ClinicalInsight)
        assert insights[0].insight_type == "ABNORMAL_LAB"

    @pytest.mark.asyncio
    async def test_acknowledge_insight(self, db: AsyncSession, doctor_user, test_patient, test_encounter):
        """Doctor should be able to acknowledge a clinical insight."""
        encounter_id = test_encounter.id
        patient_id = test_patient.id

        insight = ClinicalInsight(
            encounter_id=encounter_id,
            patient_id=patient_id,
            insight_type="GENERAL",
            title="Test Insight",
            description="Test description",
        )
        db.add(insight)
        await db.flush()

        svc = ClinicalInsightService(db)
        acked = await svc.acknowledge(insight.id, doctor_user.id)
        assert acked is not None
        assert acked.is_acknowledged is True
        assert acked.acknowledged_by == doctor_user.id


# ── Risk Detection Tests ──────────────────────────────────────────────────────


class TestRiskDetectionService:
    @pytest.mark.asyncio
    async def test_run_risk_analysis(self, db: AsyncSession, test_patient, test_encounter):
        """Should detect and persist risk alerts from Grok output."""
        import json
        encounter_id = test_encounter.id
        patient_id = test_patient.id

        with (
            patch(
                "app.core.ai.services._fetch_encounter_context",
                new=AsyncMock(return_value=MOCK_ENCOUNTER_CTX),
            ),
            patch(
                "app.core.ai.services.grok_chat",
                new=AsyncMock(return_value={"content": json.dumps(MOCK_RISK_JSON)}),
            ),
        ):
            svc = RiskDetectionService(db)
            alerts = await svc.run_risk_analysis(
                patient_id=patient_id, encounter_id=encounter_id
            )

        assert len(alerts) > 0
        assert isinstance(alerts[0], RiskAlert)
        assert alerts[0].severity == "MEDIUM"
        assert not alerts[0].is_resolved

    @pytest.mark.asyncio
    async def test_resolve_alert(self, db: AsyncSession, doctor_user, test_patient, test_encounter):
        """Doctor should be able to resolve a risk alert."""
        encounter_id = test_encounter.id
        patient_id = test_patient.id

        alert = RiskAlert(
            encounter_id=encounter_id,
            patient_id=patient_id,
            category="CLINICAL_RISK",
            severity="HIGH",
            title="Test Alert",
            description="Test",
        )
        db.add(alert)
        await db.flush()

        svc = RiskDetectionService(db)
        resolved = await svc.resolve_alert(alert.id, doctor_user.id)
        assert resolved is not None
        assert resolved.is_resolved is True
        assert resolved.resolved_by == doctor_user.id


# ── Agent Orchestration Tests ─────────────────────────────────────────────────


class TestAgentOrchestrationService:
    @pytest.mark.asyncio
    async def test_create_discharge_summary_task(self, db: AsyncSession, doctor_user):
        """Should create an agent task in AWAITING_APPROVAL status with draft content."""
        with (
            patch(
                "app.core.ai.services._fetch_encounter_context",
                new=AsyncMock(return_value=MOCK_ENCOUNTER_CTX),
            ),
            patch(
                "app.core.ai.services.grok_chat",
                new=AsyncMock(return_value={"content": MOCK_AGENT_DRAFT}),
            ),
        ):
            svc = AgentOrchestrationService(db)
            task = await svc.create_task(
                agent_type="discharge_summary",
                user_id=doctor_user.id,
                task_input={"additional_notes": "Patient improving"},
            )

        assert isinstance(task, AIAgentTask)
        assert task.status == AgentTaskStatus.AWAITING_APPROVAL
        assert task.draft_output is not None
        assert task.approved_by is None  # NOT yet approved

    @pytest.mark.asyncio
    async def test_task_requires_approval(self, db: AsyncSession, doctor_user):
        """Draft must stay in AWAITING_APPROVAL until explicitly approved."""
        with (
            patch("app.core.ai.services._fetch_encounter_context", new=AsyncMock(return_value={})),
            patch(
                "app.core.ai.services.grok_chat",
                new=AsyncMock(return_value={"content": MOCK_AGENT_DRAFT}),
            ),
        ):
            svc = AgentOrchestrationService(db)
            task = await svc.create_task(
                agent_type="documentation_draft",
                user_id=doctor_user.id,
                task_input={},
            )

        assert task.status == AgentTaskStatus.AWAITING_APPROVAL

        # Now approve
        approved = await svc.approve_task(task.id, doctor_user.id)
        assert approved is not None
        assert approved.status == AgentTaskStatus.APPROVED
        assert approved.approved_by == doctor_user.id
        assert approved.approved_at is not None

    @pytest.mark.asyncio
    async def test_approve_nonexistent_task_returns_none(self, db: AsyncSession, doctor_user):
        """Approving a non-existent task should return None."""
        svc = AgentOrchestrationService(db)
        result = await svc.approve_task(uuid.uuid4(), doctor_user.id)
        assert result is None
