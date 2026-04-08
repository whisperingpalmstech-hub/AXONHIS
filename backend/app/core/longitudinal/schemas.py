from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from uuid import UUID


class LongitudinalRecordIndexCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    record_type: str
    record_id: UUID
    record_date: datetime
    record_data: dict = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    relevance_score: Optional[float] = None
    facility_id: Optional[UUID] = None


class LongitudinalRecordIndexUpdate(BaseModel):
    record_data: Optional[dict] = None
    tags: Optional[List[str]] = None
    relevance_score: Optional[float] = None


class LongitudinalRecordIndexResponse(BaseModel):
    index_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID]
    record_type: str
    record_id: UUID
    record_date: datetime
    record_data: dict
    search_vector: Optional[str]
    tags: List[str]
    relevance_score: Optional[float]
    facility_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PatientTimelineEvent(BaseModel):
    timeline_id: UUID
    patient_id: UUID
    event_type: str
    event_date: datetime
    event_data: dict
    source_system: str
    encounter_id: Optional[UUID]
    facility_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class RecordSearchCacheCreate(BaseModel):
    patient_id: UUID
    search_key: str
    cache_data: dict = Field(default_factory=dict)
    expires_at: Optional[datetime] = None


class RecordSearchCacheResponse(BaseModel):
    cache_id: UUID
    patient_id: UUID
    search_key: str
    cache_data: dict
    hit_count: int
    last_accessed: datetime
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class PatientTimelineQuery(BaseModel):
    patient_id: UUID
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: Optional[List[str]] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class PatientTimelineResponse(BaseModel):
    patient_id: UUID
    events: List[PatientTimelineEvent]
    total_count: int
    has_more: bool


class LongitudinalRecordSearchQuery(BaseModel):
    patient_id: UUID
    record_types: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    search_text: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class LongitudinalRecordSearchResponse(BaseModel):
    patient_id: UUID
    records: List[LongitudinalRecordIndexResponse]
    total_count: int
    has_more: bool
