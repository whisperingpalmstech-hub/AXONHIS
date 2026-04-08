from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class SuggestionStatus(str, Enum):
    SUGGESTED = "SUGGESTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"
    IGNORED = "IGNORED"


class SuggestionType(str, Enum):
    QUESTION = "QUESTION"
    DIAGNOSIS = "DIAGNOSIS"
    MEDICATION = "MEDICATION"
    LAB_TEST = "LAB_TEST"
    MANAGEMENT_PLAN = "MANAGEMENT_PLAN"
    EXAM_FINDING = "EXAM_FINDING"
    DOCUMENTATION = "DOCUMENTATION"
    CLINICAL_NOTE = "CLINICAL_NOTE"


class SuggestionCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    suggestion_type: SuggestionType
    suggestion_source: str  # AI, MCP, RULE_ENGINE
    source_model: Optional[str] = None
    original_suggestion: dict = Field(default_factory=dict)
    confidence_score: Optional[float] = Field(None, ge=0, le=100)


class SuggestionUpdate(BaseModel):
    status: Optional[SuggestionStatus] = None
    modified_suggestion: Optional[dict] = None
    acceptance_reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    modification_notes: Optional[str] = None
    relevance_score: Optional[float] = Field(None, ge=0, le=100)
    responded_by: Optional[str] = None


class SuggestionResponse(BaseModel):
    suggestion_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID]
    suggestion_type: str
    suggestion_source: str
    source_model: Optional[str]
    original_suggestion: dict
    modified_suggestion: Optional[dict]
    status: SuggestionStatus
    acceptance_reason: Optional[str]
    rejection_reason: Optional[str]
    modification_notes: Optional[str]
    confidence_score: Optional[float]
    relevance_score: Optional[float]
    presented_at: datetime
    responded_at: Optional[datetime]
    responded_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SuggestionFeedbackCreate(BaseModel):
    suggestion_id: UUID
    feedback_type: str
    rating: Optional[float] = Field(None, ge=1, le=5)
    comments: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    created_by: str


class SuggestionFeedbackResponse(BaseModel):
    feedback_id: UUID
    suggestion_id: UUID
    feedback_type: str
    rating: Optional[float]
    comments: Optional[str]
    categories: List[str]
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class SuggestionAnalyticsResponse(BaseModel):
    analytics_id: UUID
    suggestion_type: str
    suggestion_source: str
    date: datetime
    total_suggested: int
    total_accepted: int
    total_rejected: int
    total_modified: int
    acceptance_rate: Optional[float]
    avg_confidence: Optional[float]
    avg_relevance: Optional[float]
    facility_id: Optional[UUID]
    specialty_profile_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SuggestionSearchQuery(BaseModel):
    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    suggestion_type: Optional[SuggestionType] = None
    suggestion_source: Optional[str] = None
    status: Optional[SuggestionStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class SuggestionSearchResponse(BaseModel):
    suggestions: List[SuggestionResponse]
    total_count: int
    has_more: bool


class SuggestionAcceptanceStats(BaseModel):
    suggestion_type: str
    suggestion_source: str
    total_suggested: int
    total_accepted: int
    total_rejected: int
    total_modified: int
    acceptance_rate: float
    avg_confidence: float
    avg_relevance: float
