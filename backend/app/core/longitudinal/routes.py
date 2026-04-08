from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.longitudinal.schemas import (
    LongitudinalRecordIndexCreate,
    LongitudinalRecordIndexUpdate,
    LongitudinalRecordIndexResponse,
    PatientTimelineQuery,
    PatientTimelineResponse,
    PatientTimelineEvent,
    LongitudinalRecordSearchQuery,
    LongitudinalRecordSearchResponse,
    RecordSearchCacheCreate,
    RecordSearchCacheResponse
)
from app.core.longitudinal.services import LongitudinalRecordService
from app.database import get_db

router = APIRouter(prefix="/longitudinal", tags=["longitudinal"])


@router.post("/records", response_model=LongitudinalRecordIndexResponse)
async def create_record_index(
    record_data: LongitudinalRecordIndexCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new longitudinal record index entry."""
    service = LongitudinalRecordService(db)
    index = await service.create_record_index(record_data)
    return index


@router.put("/records/{index_id}", response_model=LongitudinalRecordIndexResponse)
async def update_record_index(
    index_id: UUID,
    update_data: LongitudinalRecordIndexUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing longitudinal record index."""
    service = LongitudinalRecordService(db)
    index = await service.update_record_index(index_id, update_data)
    if not index:
        raise HTTPException(status_code=404, detail="Record index not found")
    return index


@router.get("/records/{index_id}", response_model=LongitudinalRecordIndexResponse)
async def get_record_index(
    index_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific longitudinal record index."""
    service = LongitudinalRecordService(db)
    index = await service.get_record_index(index_id)
    if not index:
        raise HTTPException(status_code=404, detail="Record index not found")
    return index


@router.post("/records/search", response_model=LongitudinalRecordSearchResponse)
async def search_records(
    query: LongitudinalRecordSearchQuery,
    db: AsyncSession = Depends(get_db)
):
    """Search longitudinal records with filters."""
    service = LongitudinalRecordService(db)
    records, total_count = await service.search_records(query)
    has_more = (query.offset + query.limit) < total_count
    return LongitudinalRecordSearchResponse(
        patient_id=query.patient_id,
        records=records,
        total_count=total_count,
        has_more=has_more
    )


@router.post("/timeline", response_model=PatientTimelineResponse)
async def get_patient_timeline(
    query: PatientTimelineQuery,
    db: AsyncSession = Depends(get_db)
):
    """Get patient timeline events with filters."""
    service = LongitudinalRecordService(db)
    events, total_count = await service.get_patient_timeline(query)
    has_more = (query.offset + query.limit) < total_count
    return PatientTimelineResponse(
        patient_id=query.patient_id,
        events=events,
        total_count=total_count,
        has_more=has_more
    )


@router.post("/encounters/{encounter_id}/index")
async def index_encounter(
    encounter_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Index all records from an encounter into longitudinal index."""
    service = LongitudinalRecordService(db)
    result = await service.index_encounter(encounter_id)
    return result


@router.get("/patients/{patient_id}/summary")
async def get_patient_summary(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a summary of patient's longitudinal records."""
    service = LongitudinalRecordService(db)
    summary = await service.get_patient_summary(patient_id)
    return summary


@router.get("/patients/{patient_id}/timeline", response_model=PatientTimelineResponse)
async def get_patient_timeline_by_id(
    patient_id: UUID,
    start_date: str = Query(None),
    end_date: str = Query(None),
    event_types: List[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get patient timeline by patient ID with query parameters."""
    from datetime import datetime
    
    service = LongitudinalRecordService(db)
    query = PatientTimelineQuery(
        patient_id=patient_id,
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        event_types=event_types,
        limit=limit,
        offset=offset
    )
    events, total_count = await service.get_patient_timeline(query)
    has_more = (offset + limit) < total_count
    return PatientTimelineResponse(
        patient_id=patient_id,
        events=events,
        total_count=total_count,
        has_more=has_more
    )
