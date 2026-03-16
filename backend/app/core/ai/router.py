"""
AI Router – Summary generation and voice processing endpoints.

These are stubs that will be fully implemented in Phases 11-12.
The mock-friendly design allows tests to run without real API keys.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/ai", tags=["ai"])


# ── Schemas ──────────────────────────────────────────────────────────────

class SummaryResponse(BaseModel):
    encounter_id: uuid.UUID
    narrative: str
    active_problems: list[str]
    active_medications: list[str]
    risk_alerts: list[str]


class VoiceTranscriptResponse(BaseModel):
    text: str
    language: str


class VoiceOrderSuggestion(BaseModel):
    transcript: str
    suggested_orders: list[dict[str, Any]]
    confidence: float


# ── Endpoints (stubs) ────────────────────────────────────────────────────

@router.get("/summary/{encounter_id}", response_model=SummaryResponse)
async def get_summary(encounter_id: uuid.UUID, db: DBSession, _: CurrentUser) -> SummaryResponse:
    """Generate AI patient summary from encounter timeline. (Phase 11)"""
    # Stub – returns placeholder until AI engine is integrated
    return SummaryResponse(
        encounter_id=encounter_id,
        narrative="AI summary will be generated from patient timeline events.",
        active_problems=[],
        active_medications=[],
        risk_alerts=[],
    )


@router.post("/voice/transcribe", response_model=VoiceTranscriptResponse)
async def transcribe_audio(_: CurrentUser) -> VoiceTranscriptResponse:
    """Transcribe audio to text using STT engine. (Phase 12)"""
    return VoiceTranscriptResponse(text="", language="en")


@router.post("/voice/extract-orders", response_model=VoiceOrderSuggestion)
async def extract_orders(transcript: dict, _: CurrentUser) -> VoiceOrderSuggestion:
    """Extract clinical orders from transcribed text. (Phase 12)"""
    return VoiceOrderSuggestion(
        transcript=transcript.get("text", ""),
        suggested_orders=[],
        confidence=0.0,
    )
