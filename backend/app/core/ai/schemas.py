"""
AXONHIS AI Platform – Phase 9 Pydantic Schemas.
"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Patient Summary ───────────────────────────────────────────────────────────


class PatientSummaryRequest(BaseModel):
    encounter_id: uuid.UUID


class PatientSummaryResponse(BaseModel):
    id: uuid.UUID
    encounter_id: uuid.UUID
    patient_id: uuid.UUID
    narrative: str
    primary_diagnosis: str | None = None
    active_treatments: list[str] = []
    recent_abnormal_labs: list[dict[str, Any]] = []
    pending_tests: list[str] = []
    clinical_trends: list[str] = []
    risk_flags: list[str] = []
    llm_model: str
    generated_at: datetime
    is_stale: bool = False

    model_config = {"from_attributes": True}


# ── Clinical Insights ─────────────────────────────────────────────────────────


class ClinicalInsightOut(BaseModel):
    id: uuid.UUID
    encounter_id: uuid.UUID
    patient_id: uuid.UUID
    insight_type: str
    title: str
    description: str
    recommendation: str | None = None
    confidence_score: float | None = None
    is_acknowledged: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AcknowledgeInsightRequest(BaseModel):
    insight_id: uuid.UUID


# ── Risk Alerts ───────────────────────────────────────────────────────────────


class RiskAlertOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    encounter_id: uuid.UUID | None = None
    category: str
    severity: str
    title: str
    description: str
    recommended_action: str | None = None
    is_resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ResolveAlertRequest(BaseModel):
    alert_id: uuid.UUID


# ── Voice Command ─────────────────────────────────────────────────────────────


class VoiceCommandRequest(BaseModel):
    transcript: str = Field(..., min_length=1, description="Raw transcript from STT")
    language: str = Field(default="en", description="Detected language code: en | hi | mr")
    encounter_id: uuid.UUID | None = None


class VoiceCommandResponse(BaseModel):
    id: uuid.UUID
    raw_transcript: str
    detected_language: str
    translated_text: str | None = None
    intent: str | None = None
    parsed_action: dict[str, Any]
    suggested_orders: list[dict[str, Any]]
    confidence: float
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConfirmVoiceCommandRequest(BaseModel):
    command_id: uuid.UUID


# ── AI Agent Tasks ────────────────────────────────────────────────────────────


class AgentTaskRequest(BaseModel):
    agent_type: str = Field(
        ...,
        description="One of: discharge_summary | documentation_draft | clinical_data_summary | workflow_reminder",
    )
    encounter_id: uuid.UUID | None = None
    patient_id: uuid.UUID | None = None
    task_input: dict[str, Any] = {}


class AgentTaskOut(BaseModel):
    id: uuid.UUID
    agent_type: str
    encounter_id: uuid.UUID | None = None
    patient_id: uuid.UUID | None = None
    draft_output: str | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApproveAgentTaskRequest(BaseModel):
    draft_output: str | None = None
