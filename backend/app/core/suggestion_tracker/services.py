from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from app.core.suggestion_tracker.models import (
    MdSuggestion,
    MdSuggestionFeedback,
    MdSuggestionAnalytics,
    MdSuggestionPattern,
    SuggestionStatus,
    SuggestionType
)
from app.core.suggestion_tracker.schemas import (
    SuggestionCreate,
    SuggestionUpdate,
    SuggestionFeedbackCreate,
    SuggestionSearchQuery
)


class SuggestionTrackerService:
    """Service for tracking AI suggestion acceptance and feedback."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_suggestion(
        self,
        suggestion_data: SuggestionCreate
    ) -> MdSuggestion:
        """Create a new suggestion tracking record."""
        suggestion = MdSuggestion(
            patient_id=suggestion_data.patient_id,
            encounter_id=suggestion_data.encounter_id,
            suggestion_type=suggestion_data.suggestion_type,
            suggestion_source=suggestion_data.suggestion_source,
            source_model=suggestion_data.source_model,
            original_suggestion=suggestion_data.original_suggestion,
            confidence_score=suggestion_data.confidence_score
        )
        self.db.add(suggestion)
        await self.db.commit()
        await self.db.refresh(suggestion)
        return suggestion

    async def update_suggestion(
        self,
        suggestion_id: uuid.UUID,
        update_data: SuggestionUpdate
    ) -> Optional[MdSuggestion]:
        """Update a suggestion with response status."""
        query = select(MdSuggestion).where(MdSuggestion.suggestion_id == suggestion_id)
        result = await self.db.execute(query)
        suggestion = result.scalar_one_or_none()
        
        if not suggestion:
            return None
        
        if update_data.status is not None:
            suggestion.status = update_data.status
            suggestion.responded_at = datetime.utcnow()
        
        if update_data.modified_suggestion is not None:
            suggestion.modified_suggestion = update_data.modified_suggestion
        
        if update_data.acceptance_reason is not None:
            suggestion.acceptance_reason = update_data.acceptance_reason
        
        if update_data.rejection_reason is not None:
            suggestion.rejection_reason = update_data.rejection_reason
        
        if update_data.modification_notes is not None:
            suggestion.modification_notes = update_data.modification_notes
        
        if update_data.relevance_score is not None:
            suggestion.relevance_score = update_data.relevance_score
        
        if update_data.responded_by is not None:
            suggestion.responded_by = update_data.responded_by
        
        await self.db.commit()
        await self.db.refresh(suggestion)
        
        # Update analytics
        await self._update_analytics(suggestion)
        
        return suggestion

    async def get_suggestion(
        self,
        suggestion_id: uuid.UUID
    ) -> Optional[MdSuggestion]:
        """Get a specific suggestion."""
        query = select(MdSuggestion).where(MdSuggestion.suggestion_id == suggestion_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def search_suggestions(
        self,
        query: SuggestionSearchQuery
    ) -> tuple[List[MdSuggestion], int]:
        """Search suggestions with filters."""
        conditions = []
        
        if query.patient_id:
            conditions.append(MdSuggestion.patient_id == query.patient_id)
        
        if query.encounter_id:
            conditions.append(MdSuggestion.encounter_id == query.encounter_id)
        
        if query.suggestion_type:
            conditions.append(MdSuggestion.suggestion_type == query.suggestion_type)
        
        if query.suggestion_source:
            conditions.append(MdSuggestion.suggestion_source == query.suggestion_source)
        
        if query.status:
            conditions.append(MdSuggestion.status == query.status)
        
        if query.start_date:
            conditions.append(MdSuggestion.presented_at >= query.start_date)
        
        if query.end_date:
            conditions.append(MdSuggestion.presented_at <= query.end_date)
        
        # Get total count
        count_query = select(func.count(MdSuggestion.suggestion_id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()
        
        # Get paginated results
        suggestions_query = select(MdSuggestion)
        if conditions:
            suggestions_query = suggestions_query.where(and_(*conditions))
        
        suggestions_query = suggestions_query.order_by(desc(MdSuggestion.presented_at)).offset(
            query.offset
        ).limit(query.limit)
        
        suggestions_result = await self.db.execute(suggestions_query)
        suggestions = suggestions_result.scalars().all()
        
        return list(suggestions), total_count

    async def add_feedback(
        self,
        feedback_data: SuggestionFeedbackCreate
    ) -> MdSuggestionFeedback:
        """Add feedback to a suggestion."""
        feedback = MdSuggestionFeedback(
            suggestion_id=feedback_data.suggestion_id,
            feedback_type=feedback_data.feedback_type,
            rating=feedback_data.rating,
            comments=feedback_data.comments,
            categories=feedback_data.categories,
            created_by=feedback_data.created_by
        )
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback

    async def get_suggestion_feedback(
        self,
        suggestion_id: uuid.UUID
    ) -> List[MdSuggestionFeedback]:
        """Get all feedback for a suggestion."""
        query = select(MdSuggestionFeedback).where(
            MdSuggestionFeedback.suggestion_id == suggestion_id
        ).order_by(desc(MdSuggestionFeedback.created_at))
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_acceptance_stats(
        self,
        suggestion_type: Optional[str] = None,
        suggestion_source: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get acceptance statistics for suggestions."""
        conditions = []
        
        if suggestion_type:
            conditions.append(MdSuggestion.suggestion_type == suggestion_type)
        
        if suggestion_source:
            conditions.append(MdSuggestion.suggestion_source == suggestion_source)
        
        if start_date:
            conditions.append(MdSuggestion.presented_at >= start_date)
        
        if end_date:
            conditions.append(MdSuggestion.presented_at <= end_date)
        
        # Get counts by status
        base_query = select(MdSuggestion)
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        total_result = await self.db.execute(select(func.count()).select_from(base_query))
        total_suggested = total_result.scalar() or 0
        
        accepted_query = base_query.where(MdSuggestion.status == SuggestionStatus.ACCEPTED)
        accepted_result = await self.db.execute(select(func.count()).select_from(accepted_query))
        total_accepted = accepted_result.scalar() or 0
        
        rejected_query = base_query.where(MdSuggestion.status == SuggestionStatus.REJECTED)
        rejected_result = await self.db.execute(select(func.count()).select_from(rejected_query))
        total_rejected = rejected_result.scalar() or 0
        
        modified_query = base_query.where(MdSuggestion.status == SuggestionStatus.MODIFIED)
        modified_result = await self.db.execute(select(func.count()).select_from(modified_query))
        total_modified = modified_result.scalar() or 0
        
        # Get average confidence
        confidence_query = select(func.avg(MdSuggestion.confidence_score))
        if conditions:
            confidence_query = confidence_query.where(and_(*conditions))
        confidence_result = await self.db.execute(confidence_query)
        avg_confidence = confidence_result.scalar() or 0
        
        # Get average relevance
        relevance_query = select(func.avg(MdSuggestion.relevance_score))
        if conditions:
            relevance_query = relevance_query.where(and_(*conditions))
        relevance_result = await self.db.execute(relevance_query)
        avg_relevance = relevance_result.scalar() or 0
        
        acceptance_rate = (total_accepted / total_suggested * 100) if total_suggested > 0 else 0
        
        return {
            "suggestion_type": suggestion_type,
            "suggestion_source": suggestion_source,
            "total_suggested": total_suggested,
            "total_accepted": total_accepted,
            "total_rejected": total_rejected,
            "total_modified": total_modified,
            "acceptance_rate": round(acceptance_rate, 2),
            "avg_confidence": round(float(avg_confidence), 2),
            "avg_relevance": round(float(avg_relevance), 2)
        }

    async def _update_analytics(
        self,
        suggestion: MdSuggestion
    ):
        """Update analytics when a suggestion status changes."""
        today = datetime.utcnow().date()
        
        # Check if analytics record exists for today
        query = select(MdSuggestionAnalytics).where(
            and_(
                MdSuggestionAnalytics.suggestion_type == suggestion.suggestion_type,
                MdSuggestionAnalytics.suggestion_source == suggestion.suggestion_source,
                func.date(MdSuggestionAnalytics.date) == today
            )
        )
        
        result = await self.db.execute(query)
        analytics = result.scalar_one_or_none()
        
        if not analytics:
            # Create new analytics record
            analytics = MdSuggestionAnalytics(
                suggestion_type=suggestion.suggestion_type,
                suggestion_source=suggestion.suggestion_source,
                date=datetime.utcnow()
            )
            self.db.add(analytics)
        
        # Update counts
        if suggestion.status == SuggestionStatus.ACCEPTED:
            analytics.total_accepted += 1
        elif suggestion.status == SuggestionStatus.REJECTED:
            analytics.total_rejected += 1
        elif suggestion.status == SuggestionStatus.MODIFIED:
            analytics.total_modified += 1
        
        analytics.total_suggested += 1
        analytics.updated_at = datetime.utcnow()
        
        # Recalculate rates
        if analytics.total_suggested > 0:
            analytics.acceptance_rate = (analytics.total_accepted / analytics.total_suggested) * 100
        
        await self.db.commit()

    async def get_patient_suggestion_history(
        self,
        patient_id: uuid.UUID,
        limit: int = 100
    ) -> List[MdSuggestion]:
        """Get suggestion history for a patient."""
        query = select(MdSuggestion).where(
            MdSuggestion.patient_id == patient_id
        ).order_by(desc(MdSuggestion.presented_at)).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_encounter_suggestions(
        self,
        encounter_id: uuid.UUID
    ) -> List[MdSuggestion]:
        """Get all suggestions for an encounter."""
        query = select(MdSuggestion).where(
            MdSuggestion.encounter_id == encounter_id
        ).order_by(desc(MdSuggestion.presented_at))
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def bulk_create_suggestions(
        self,
        suggestions: List[SuggestionCreate]
    ) -> List[MdSuggestion]:
        """Create multiple suggestions in bulk."""
        created_suggestions = []
        
        for suggestion_data in suggestions:
            suggestion = await self.create_suggestion(suggestion_data)
            created_suggestions.append(suggestion)
        
        return created_suggestions
