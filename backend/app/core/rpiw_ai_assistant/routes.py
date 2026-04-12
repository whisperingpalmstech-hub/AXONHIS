from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from .schemas import (
    GenerateAiResponseRequest, AiSuggestionOut, AiAlertOut, 
    AiFeedbackCreate, AiFeedbackOut
)
from .services import RpiwAiService

router = APIRouter(prefix="/api/v1/rpiw-ai", tags=["RPIW - AI Assistant Engine"])

@router.post("/generate", response_model=dict)
async def generate_ai_insights(req: GenerateAiResponseRequest, db: AsyncSession = Depends(get_db)):
    """Analyze context and generate specialized AI suggestions and alerts."""
    svc = RpiwAiService(db)
    result = await svc.gather_context_and_generate(req.patient_uhid, req.user_id, req.role_code)
    # Re-fetch state so it uses Pydantic schema mapping easily, but mapping manually is fine here:
    return {
       "alerts": [AiAlertOut.model_validate(a).model_dump() for a in result["alerts"]],
       "suggestions": [AiSuggestionOut.model_validate(s).model_dump() for s in result["suggestions"]]
    }

@router.get("/state/{patient_uhid}/{role_code}", response_model=dict)
async def get_current_ai_state(patient_uhid: str, role_code: str, db: AsyncSession = Depends(get_db)):
    """Fetch active alerts and pending suggestions for the workspace AI panel."""
    svc = RpiwAiService(db)
    state = await svc.get_patient_ai_state(patient_uhid, role_code)
    return {
       "alerts": [AiAlertOut.model_validate(a).model_dump() for a in state["alerts"]],
       "suggestions": [AiSuggestionOut.model_validate(s).model_dump() for s in state["suggestions"]]
    }

@router.post("/suggestions/{suggestion_id}/action", response_model=AiSuggestionOut)
async def act_on_suggestion(suggestion_id: str, action: str, user_id: str, role_code: str, db: AsyncSession = Depends(get_db)):
    """Accept or Reject a suggestion."""
    svc = RpiwAiService(db)
    if action.lower() not in ["accept", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'accept' or 'reject'")
    sugg = await svc.handle_suggestion_action(suggestion_id, action, user_id, role_code)
    if not sugg:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return sugg

@router.post("/suggestions/{suggestion_id}/feedback", response_model=AiFeedbackOut)
async def submit_ai_feedback(suggestion_id: str, feedback: AiFeedbackCreate, db: AsyncSession = Depends(get_db)):
    """Submit quality feedback for continuous learning."""
    svc = RpiwAiService(db)
    fb = await svc.submit_feedback(suggestion_id, feedback)
    return fb

