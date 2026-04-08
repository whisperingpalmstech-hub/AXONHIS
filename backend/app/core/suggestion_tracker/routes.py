from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.suggestion_tracker.schemas import (
    SuggestionCreate,
    SuggestionUpdate,
    SuggestionResponse,
    SuggestionFeedbackCreate,
    SuggestionFeedbackResponse,
    SuggestionSearchQuery,
    SuggestionSearchResponse,
    SuggestionAcceptanceStats
)
from app.core.suggestion_tracker.services import SuggestionTrackerService
from app.database import get_db

router = APIRouter(prefix="/suggestion-tracker", tags=["suggestion-tracker"])


@router.post("/suggestions", response_model=SuggestionResponse)
async def create_suggestion(
    suggestion_data: SuggestionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new suggestion tracking record."""
    service = SuggestionTrackerService(db)
    suggestion = await service.create_suggestion(suggestion_data)
    return suggestion


@router.put("/suggestions/{suggestion_id}", response_model=SuggestionResponse)
async def update_suggestion(
    suggestion_id: UUID,
    update_data: SuggestionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a suggestion with response status."""
    service = SuggestionTrackerService(db)
    suggestion = await service.update_suggestion(suggestion_id, update_data)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return suggestion


@router.get("/suggestions/{suggestion_id}", response_model=SuggestionResponse)
async def get_suggestion(
    suggestion_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific suggestion."""
    service = SuggestionTrackerService(db)
    suggestion = await service.get_suggestion(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return suggestion


@router.post("/suggestions/search", response_model=SuggestionSearchResponse)
async def search_suggestions(
    query: SuggestionSearchQuery,
    db: AsyncSession = Depends(get_db)
):
    """Search suggestions with filters."""
    service = SuggestionTrackerService(db)
    suggestions, total_count = await service.search_suggestions(query)
    has_more = (query.offset + query.limit) < total_count
    return SuggestionSearchResponse(
        suggestions=suggestions,
        total_count=total_count,
        has_more=has_more
    )


@router.post("/suggestions/{suggestion_id}/feedback", response_model=SuggestionFeedbackResponse)
async def add_feedback(
    suggestion_id: UUID,
    feedback_data: SuggestionFeedbackCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add feedback to a suggestion."""
    service = SuggestionTrackerService(db)
    feedback_data.suggestion_id = suggestion_id
    feedback = await service.add_feedback(feedback_data)
    return feedback


@router.get("/suggestions/{suggestion_id}/feedback", response_model=List[SuggestionFeedbackResponse])
async def get_suggestion_feedback(
    suggestion_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all feedback for a suggestion."""
    service = SuggestionTrackerService(db)
    feedback = await service.get_suggestion_feedback(suggestion_id)
    return feedback


@router.get("/patients/{patient_id}/suggestions", response_model=List[SuggestionResponse])
async def get_patient_suggestion_history(
    patient_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get suggestion history for a patient."""
    service = SuggestionTrackerService(db)
    suggestions = await service.get_patient_suggestion_history(patient_id, limit)
    return suggestions


@router.get("/encounters/{encounter_id}/suggestions", response_model=List[SuggestionResponse])
async def get_encounter_suggestions(
    encounter_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all suggestions for an encounter."""
    service = SuggestionTrackerService(db)
    suggestions = await service.get_encounter_suggestions(encounter_id)
    return suggestions


@router.get("/analytics/acceptance-stats", response_model=SuggestionAcceptanceStats)
async def get_acceptance_stats(
    suggestion_type: str = Query(None),
    suggestion_source: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get acceptance statistics for suggestions."""
    from datetime import datetime
    
    service = SuggestionTrackerService(db)
    
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    stats = await service.get_acceptance_stats(
        suggestion_type=suggestion_type,
        suggestion_source=suggestion_source,
        start_date=start_dt,
        end_date=end_dt
    )
    return stats
