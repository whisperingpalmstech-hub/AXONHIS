from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, backref

from app.database import Base


class MdLongitudinalRecordIndex(Base):
    """
    Longitudinal Record Index for fast retrieval across patient history.
    Provides indexed access to patient records across encounters, documents,
    diagnoses, medications, and other clinical data.
    """
    __tablename__ = "md_longitudinal_record_index"

    index_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=True, index=True)
    record_type = Column(String(50), nullable=False, index=True)  # encounter, diagnosis, medication, lab_result, document, etc.
    record_id = Column(UUID(as_uuid=True), nullable=False)
    record_date = Column(DateTime, nullable=False, index=True)
    record_data = Column(JSONB, nullable=False, default={})
    search_vector = Column(Text, nullable=True)  # Full-text search vector
    tags = Column(JSONB, nullable=False, default=[])  # Tags for categorization
    relevance_score = Column(Numeric(5,2), nullable=True)  # AI-generated relevance score
    facility_id = Column(UUID(as_uuid=True), ForeignKey("md_facility.facility_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", backref=backref("longitudinal_records", cascade="all, delete-orphan"))
    encounter = relationship("MdEncounter", backref="longitudinal_records")

    __table_args__ = (
        Index('idx_longitudinal_patient_date', 'patient_id', 'record_date'),
        Index('idx_longitudinal_type_date', 'record_type', 'record_date'),
        Index('idx_longitudinal_patient_type', 'patient_id', 'record_type'),
    )


class MdPatientTimeline(Base):
    """
    Patient Timeline for chronological view of all clinical events.
    Aggregates events from encounters, labs, medications, and other systems.
    """
    __tablename__ = "md_patient_timeline"

    timeline_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # encounter, diagnosis, lab, medication, etc.
    event_date = Column(DateTime, nullable=False, index=True)
    event_data = Column(JSONB, nullable=False, default={})
    source_system = Column(String(50), nullable=False)  # encounter, lab, pharmacy, etc.
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id"), nullable=True)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("md_facility.facility_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", backref=backref("timeline_events", cascade="all, delete-orphan"))
    encounter = relationship("MdEncounter", backref="timeline_events")

    __table_args__ = (
        Index('idx_timeline_patient_date', 'patient_id', 'event_date'),
        Index('idx_timeline_type_date', 'event_type', 'event_date'),
    )


class MdRecordSearchCache(Base):
    """
    Cache for frequently searched patient records.
    Improves performance of common search queries.
    """
    __tablename__ = "md_record_search_cache"

    cache_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    search_key = Column(String(255), nullable=False, index=True)
    cache_data = Column(JSONB, nullable=False, default={})
    hit_count = Column(Numeric(10,0), default=0, nullable=False)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("Patient", backref=backref("search_cache", cascade="all, delete-orphan"))

    __table_args__ = (
        Index('idx_cache_patient_key', 'patient_id', 'search_key'),
        Index('idx_cache_expires', 'expires_at'),
    )
