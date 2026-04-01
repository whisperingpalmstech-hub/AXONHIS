"""
AXONHIS Virtual Avatar – Pydantic Schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Session ──────────────────────────────────────────────────────────────────

class AvatarSessionCreate(BaseModel):
    language: str = Field(default="en", max_length=10)


class AvatarSessionOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    language: str
    status: str
    patient_id: uuid.UUID | None = None
    current_workflow: str | None = None
    workflow_step: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Messages ─────────────────────────────────────────────────────────────────

class AvatarMessageOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    intent: str | None = None
    workflow: str | None = None
    entities: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Chat / Converse ──────────────────────────────────────────────────────────

class AvatarChatRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class AvatarConverseRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64-encoded audio (webm/opus or wav)")


class AvatarConverseResponse(BaseModel):
    transcription: str
    response_text: str
    audio_base64: str | None = None
    intent: str | None = None
    workflow: str | None = None
    workflow_status: dict[str, Any] | None = None
    entities: dict[str, Any] | None = None


class AvatarChatResponse(BaseModel):
    response_text: str
    audio_base64: str | None = None
    intent: str | None = None
    workflow: str | None = None
    workflow_status: dict[str, Any] | None = None
    entities: dict[str, Any] | None = None


# ── Speech ───────────────────────────────────────────────────────────────────

class AvatarSTTRequest(BaseModel):
    audio_base64: str


class AvatarSTTResponse(BaseModel):
    transcription: str
    language: str
    confidence: float = 0.0


class AvatarTTSRequest(BaseModel):
    text: str
    language: str = "en"


class AvatarTTSResponse(BaseModel):
    audio_base64: str
    language: str


# ── Workflow Config (Admin) ──────────────────────────────────────────────────

class AvatarWorkflowConfigOut(BaseModel):
    id: uuid.UUID
    workflow_key: str
    display_name: str
    description: str | None = None
    is_enabled: bool
    icon: str | None = None
    system_prompt_override: str | None = None
    supported_languages: str | None = None
    display_order: int = 0

    model_config = {"from_attributes": True}


class AvatarWorkflowConfigUpdate(BaseModel):
    is_enabled: bool | None = None
    display_name: str | None = None
    description: str | None = None
    system_prompt_override: str | None = None
    supported_languages: str | None = None
    display_order: int | None = None


# ── Analytics ────────────────────────────────────────────────────────────────

class AvatarAnalyticsOut(BaseModel):
    total_sessions: int = 0
    active_sessions: int = 0
    total_messages: int = 0
    avg_messages_per_session: float = 0.0
    top_workflows: list[dict[str, Any]] = []
    language_distribution: list[dict[str, Any]] = []
    daily_sessions: list[dict[str, Any]] = []
