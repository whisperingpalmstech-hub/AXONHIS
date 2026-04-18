from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base
from app.core.axonhis_md.models import MdPatient, MdEncounter

class SuggestionStatus(str, enum.Enum):
    SUGGESTED = "SUGGESTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"
    IGNORED = "IGNORED"


class SuggestionType(str, enum.Enum):
    QUESTION = "QUESTION"
    DIAGNOSIS = "DIAGNOSIS"
    MEDICATION = "MEDICATION"
    LAB_TEST = "LAB_TEST"
    MANAGEMENT_PLAN = "MANAGEMENT_PLAN"
    EXAM_FINDING = "EXAM_FINDING"
    DOCUMENTATION = "DOCUMENTATION"
    CLINICAL_NOTE = "CLINICAL_NOTE"


class MdSuggestion(Base):
    """
    Suggestion tracking model for AI-generated suggestions.
    Tracks which AI suggestions are accepted, rejected, or modified by clinicians.
    """
    __tablename__ = "md_suggestion"

    suggestion_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("md_patient.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=True, index=True)
    suggestion_type = Column(String(50), nullable=False, index=True)
    suggestion_source = Column(String(50), nullable=False)  # AI, MCP, RULE_ENGINE
    source_model = Column(String(100), nullable=True)  # AI model name or rule ID
    original_suggestion = Column(JSONB, nullable=False, default={})
    modified_suggestion = Column(JSONB, nullable=True)
    status = Column(String(30), default=SuggestionStatus.SUGGESTED, nullable=False, index=True)
    acceptance_reason = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    modification_notes = Column(Text, nullable=True)
    confidence_score = Column(Numeric(5,2), nullable=True)  # AI confidence 0-100
    relevance_score = Column(Numeric(5,2), nullable=True)  # Clinician relevance 0-100
    presented_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)
    responded_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("MdPatient", backref="suggestions")
    encounter = relationship("MdEncounter", backref="suggestions")

    __table_args__ = (
        Index('idx_suggestion_patient_status', 'patient_id', 'status'),
        Index('idx_suggestion_type_status', 'suggestion_type', 'status'),
        Index('idx_suggestion_encounter', 'encounter_id', 'presented_at'),
    )


class MdSuggestionFeedback(Base):
    """
    Detailed feedback model for suggestions.
    Captures detailed feedback on why suggestions were accepted or rejected.
    """
    __tablename__ = "md_suggestion_feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suggestion_id = Column(UUID(as_uuid=True), ForeignKey("md_suggestion.suggestion_id", ondelete="CASCADE"), nullable=False, index=True)
    feedback_type = Column(String(50), nullable=False)  # ACCURACY, RELEVANCE, COMPLETENESS, TIMING, OTHER
    rating = Column(Numeric(3,1), nullable=True)  # 1-5 rating
    comments = Column(Text, nullable=True)
    categories = Column(JSONB, nullable=False, default=[])  # Tags for categorization
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    suggestion = relationship("MdSuggestion", backref="feedback")


class MdSuggestionAnalytics(Base):
    """
    Aggregated analytics for suggestion performance.
    Tracks acceptance rates, patterns, and trends.
    """
    __tablename__ = "md_suggestion_analytics"

    analytics_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suggestion_type = Column(String(50), nullable=False, index=True)
    suggestion_source = Column(String(50), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    total_suggested = Column(Numeric(10,0), default=0, nullable=False)
    total_accepted = Column(Numeric(10,0), default=0, nullable=False)
    total_rejected = Column(Numeric(10,0), default=0, nullable=False)
    total_modified = Column(Numeric(10,0), default=0, nullable=False)
    acceptance_rate = Column(Numeric(5,2), nullable=True)
    avg_confidence = Column(Numeric(5,2), nullable=True)
    avg_relevance = Column(Numeric(5,2), nullable=True)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("md_facility.facility_id"), nullable=True)
    specialty_profile_id = Column(UUID(as_uuid=True), ForeignKey("md_specialty_profile.specialty_profile_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_analytics_type_date', 'suggestion_type', 'date'),
        Index('idx_analytics_source_date', 'suggestion_source', 'date'),
    )


class MdSuggestionPattern(Base):
    """
    Pattern detection model for suggestion acceptance patterns.
    Identifies trends in suggestion acceptance over time.
    """
    __tablename__ = "md_suggestion_pattern"

    pattern_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_name = Column(String(255), nullable=False)
    pattern_type = Column(String(50), nullable=False)  # TIME_OF_DAY, SPECIALTY, ENCOUNTER_TYPE, etc.
    pattern_data = Column(JSONB, nullable=False, default={})
    acceptance_rate = Column(Numeric(5,2), nullable=True)
    sample_size = Column(Numeric(10,0), nullable=False)
    confidence = Column(Numeric(5,2), nullable=True)
    is_significant = Column(Boolean, default=False, nullable=False)
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
