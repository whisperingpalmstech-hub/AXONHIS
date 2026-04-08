from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, text
from sqlalchemy.orm import selectinload

from app.core.longitudinal.models import (
    MdLongitudinalRecordIndex,
    MdPatientTimeline,
    MdRecordSearchCache
)
from app.core.longitudinal.schemas import (
    LongitudinalRecordIndexCreate,
    LongitudinalRecordIndexUpdate,
    PatientTimelineQuery,
    LongitudinalRecordSearchQuery,
    RecordSearchCacheCreate
)


class LongitudinalRecordService:
    """Service for managing longitudinal patient records and timeline."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_record_index(
        self,
        record_data: LongitudinalRecordIndexCreate
    ) -> MdLongitudinalRecordIndex:
        """Create a new longitudinal record index entry."""
        index = MdLongitudinalRecordIndex(
            patient_id=record_data.patient_id,
            encounter_id=record_data.encounter_id,
            record_type=record_data.record_type,
            record_id=record_data.record_id,
            record_date=record_data.record_date,
            record_data=record_data.record_data,
            tags=record_data.tags,
            relevance_score=record_data.relevance_score,
            facility_id=record_data.facility_id
        )
        self.db.add(index)
        await self.db.commit()
        await self.db.refresh(index)
        
        # Also add to timeline
        await self._add_to_timeline(
            patient_id=record_data.patient_id,
            event_type=record_data.record_type,
            event_date=record_data.record_date,
            event_data=record_data.record_data,
            source_system="encounter",
            encounter_id=record_data.encounter_id,
            facility_id=record_data.facility_id
        )
        
        return index

    async def update_record_index(
        self,
        index_id: uuid.UUID,
        update_data: LongitudinalRecordIndexUpdate
    ) -> Optional[MdLongitudinalRecordIndex]:
        """Update an existing longitudinal record index."""
        query = select(MdLongitudinalRecordIndex).where(
            MdLongitudinalRecordIndex.index_id == index_id
        )
        result = await self.db.execute(query)
        index = result.scalar_one_or_none()
        
        if not index:
            return None
        
        if update_data.record_data is not None:
            index.record_data = update_data.record_data
        if update_data.tags is not None:
            index.tags = update_data.tags
        if update_data.relevance_score is not None:
            index.relevance_score = update_data.relevance_score
        
        index.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(index)
        return index

    async def get_record_index(
        self,
        index_id: uuid.UUID
    ) -> Optional[MdLongitudinalRecordIndex]:
        """Get a specific longitudinal record index."""
        query = select(MdLongitudinalRecordIndex).where(
            MdLongitudinalRecordIndex.index_id == index_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def search_records(
        self,
        query: LongitudinalRecordSearchQuery
    ) -> tuple[List[MdLongitudinalRecordIndex], int]:
        """Search longitudinal records with filters."""
        conditions = [MdLongitudinalRecordIndex.patient_id == query.patient_id]
        
        if query.record_types:
            conditions.append(MdLongitudinalRecordIndex.record_type.in_(query.record_types))
        
        if query.start_date:
            conditions.append(MdLongitudinalRecordIndex.record_date >= query.start_date)
        
        if query.end_date:
            conditions.append(MdLongitudinalRecordIndex.record_date <= query.end_date)
        
        if query.tags:
            for tag in query.tags:
                conditions.append(MdLongitudinalRecordIndex.tags.contains([tag]))
        
        if query.search_text:
            conditions.append(
                or_(
                    MdLongitudinalRecordIndex.search_vector.ilike(f"%{query.search_text}%"),
                    MdLongitudinalRecordIndex.record_data.cast(String).ilike(f"%{query.search_text}%")
                )
            )
        
        # Get total count
        count_query = select(func.count(MdLongitudinalRecordIndex.index_id)).where(
            and_(*conditions)
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()
        
        # Get paginated results
        records_query = select(MdLongitudinalRecordIndex).where(
            and_(*conditions)
        ).order_by(desc(MdLongitudinalRecordIndex.record_date)).offset(
            query.offset
        ).limit(query.limit)
        
        records_result = await self.db.execute(records_query)
        records = records_result.scalars().all()
        
        return list(records), total_count

    async def get_patient_timeline(
        self,
        query: PatientTimelineQuery
    ) -> tuple[List[MdPatientTimeline], int]:
        """Get patient timeline events with filters."""
        conditions = [MdPatientTimeline.patient_id == query.patient_id]
        
        if query.start_date:
            conditions.append(MdPatientTimeline.event_date >= query.start_date)
        
        if query.end_date:
            conditions.append(MdPatientTimeline.event_date <= query.end_date)
        
        if query.event_types:
            conditions.append(MdPatientTimeline.event_type.in_(query.event_types))
        
        # Get total count
        count_query = select(func.count(MdPatientTimeline.timeline_id)).where(
            and_(*conditions)
        )
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()
        
        # Get paginated results
        timeline_query = select(MdPatientTimeline).where(
            and_(*conditions)
        ).order_by(desc(MdPatientTimeline.event_date)).offset(
            query.offset
        ).limit(query.limit)
        
        timeline_result = await self.db.execute(timeline_query)
        events = timeline_result.scalars().all()
        
        return list(events), total_count

    async def _add_to_timeline(
        self,
        patient_id: uuid.UUID,
        event_type: str,
        event_date: datetime,
        event_data: Dict[str, Any],
        source_system: str,
        encounter_id: Optional[uuid.UUID] = None,
        facility_id: Optional[uuid.UUID] = None
    ) -> MdPatientTimeline:
        """Add an event to the patient timeline."""
        timeline_event = MdPatientTimeline(
            patient_id=patient_id,
            event_type=event_type,
            event_date=event_date,
            event_data=event_data,
            source_system=source_system,
            encounter_id=encounter_id,
            facility_id=facility_id
        )
        self.db.add(timeline_event)
        await self.db.commit()
        await self.db.refresh(timeline_event)
        return timeline_event

    async def get_search_cache(
        self,
        patient_id: uuid.UUID,
        search_key: str
    ) -> Optional[MdRecordSearchCache]:
        """Get cached search results."""
        query = select(MdRecordSearchCache).where(
            and_(
                MdRecordSearchCache.patient_id == patient_id,
                MdRecordSearchCache.search_key == search_key,
                or_(
                    MdRecordSearchCache.expires_at.is_(None),
                    MdRecordSearchCache.expires_at > datetime.utcnow()
                )
            )
        )
        result = await self.db.execute(query)
        cache = result.scalar_one_or_none()
        
        if cache:
            # Update hit count and last accessed
            cache.hit_count = (cache.hit_count or 0) + 1
            cache.last_accessed = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(cache)
        
        return cache

    async def set_search_cache(
        self,
        cache_data: RecordSearchCacheCreate,
        cache_value: Dict[str, Any]
    ) -> MdRecordSearchCache:
        """Set search cache with expiration."""
        cache = MdRecordSearchCache(
            patient_id=cache_data.patient_id,
            search_key=cache_data.search_key,
            cache_data=cache_value,
            expires_at=cache_data.expires_at or datetime.utcnow() + timedelta(hours=24)
        )
        self.db.add(cache)
        await self.db.commit()
        await self.db.refresh(cache)
        return cache

    async def index_encounter(self, encounter_id: uuid.UUID) -> Dict[str, int]:
        """Index all records from an encounter into longitudinal index."""
        from app.core.axonhis_md.models import MdEncounter, MdDiagnosis, MdMedicationRequest, MdServiceRequest
        from app.core.files.models import MdDocument
        
        # Get encounter
        encounter_query = select(MdEncounter).where(MdEncounter.encounter_id == encounter_id)
        encounter_result = await self.db.execute(encounter_query)
        encounter = encounter_result.scalar_one_or_none()
        
        if not encounter:
            return {"error": "Encounter not found"}
        
        indexed_count = 0
        
        # Index encounter itself
        await self.create_record_index(
            LongitudinalRecordIndexCreate(
                patient_id=encounter.patient_id,
                encounter_id=encounter_id,
                record_type="encounter",
                record_id=encounter_id,
                record_date=encounter.started_at,
                record_data={
                    "encounter_id": str(encounter_id),
                    "encounter_mode": encounter.encounter_mode,
                    "encounter_status": encounter.encounter_status,
                    "chief_complaint": encounter.chief_complaint
                },
                tags=["encounter", encounter.encounter_mode],
                facility_id=encounter.facility_id
            )
        )
        indexed_count += 1
        
        # Index diagnoses
        diagnoses_query = select(MdDiagnosis).where(MdDiagnosis.encounter_id == encounter_id)
        diagnoses_result = await self.db.execute(diagnoses_query)
        diagnoses = diagnoses_result.scalars().all()
        
        for diagnosis in diagnoses:
            await self.create_record_index(
                LongitudinalRecordIndexCreate(
                    patient_id=encounter.patient_id,
                    encounter_id=encounter_id,
                    record_type="diagnosis",
                    record_id=diagnosis.diagnosis_id,
                    record_date=diagnosis.created_at,
                    record_data={
                        "diagnosis_id": str(diagnosis.diagnosis_id),
                        "diagnosis_code": diagnosis.diagnosis_code,
                        "diagnosis_display": diagnosis.diagnosis_display,
                        "diagnosis_type": diagnosis.diagnosis_type,
                        "probability_score": float(diagnosis.probability_score) if diagnosis.probability_score else None
                    },
                    tags=["diagnosis", diagnosis.diagnosis_type],
                    facility_id=encounter.facility_id
                )
            )
            indexed_count += 1
        
        # Index medications
        medications_query = select(MdMedicationRequest).where(
            MdMedicationRequest.encounter_id == encounter_id
        )
        medications_result = await self.db.execute(medications_query)
        medications = medications_result.scalars().all()
        
        for medication in medications:
            await self.create_record_index(
                LongitudinalRecordIndexCreate(
                    patient_id=encounter.patient_id,
                    encounter_id=encounter_id,
                    record_type="medication",
                    record_id=medication.medication_request_id,
                    record_date=medication.created_at,
                    record_data={
                        "medication_id": str(medication.medication_request_id),
                        "medication_name": medication.medication_name,
                        "medication_code": medication.medication_code,
                        "dose": medication.dose,
                        "frequency": medication.frequency,
                        "route": medication.route
                    },
                    tags=["medication"],
                    facility_id=encounter.facility_id
                )
            )
            indexed_count += 1
        
        # Index service requests (lab tests, imaging, etc.)
        service_requests_query = select(MdServiceRequest).where(
            MdServiceRequest.encounter_id == encounter_id
        )
        service_requests_result = await self.db.execute(service_requests_query)
        service_requests = service_requests_result.scalars().all()
        
        for service_request in service_requests:
            await self.create_record_index(
                LongitudinalRecordIndexCreate(
                    patient_id=encounter.patient_id,
                    encounter_id=encounter_id,
                    record_type=service_request.request_type.lower(),
                    record_id=service_request.service_request_id,
                    record_date=service_request.created_at,
                    record_data={
                        "service_request_id": str(service_request.service_request_id),
                        "request_type": service_request.request_type,
                        "catalog_code": service_request.catalog_code,
                        "catalog_name": service_request.catalog_name,
                        "priority": service_request.priority
                    },
                    tags=["service_request", service_request.request_type.lower()],
                    facility_id=encounter.facility_id
                )
            )
            indexed_count += 1
        
        return {
            "indexed_count": indexed_count,
            "encounter_id": str(encounter_id),
            "patient_id": str(encounter.patient_id)
        }

    async def get_patient_summary(
        self,
        patient_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get a summary of patient's longitudinal records."""
        # Get counts by record type
        type_counts_query = select(
            MdLongitudinalRecordIndex.record_type,
            func.count(MdLongitudinalRecordIndex.index_id)
        ).where(
            MdLongitudinalRecordIndex.patient_id == patient_id
        ).group_by(MdLongitudinalRecordIndex.record_type)
        
        type_counts_result = await self.db.execute(type_counts_query)
        type_counts = {row[0]: row[1] for row in type_counts_result.all()}
        
        # Get date range
        date_range_query = select(
            func.min(MdLongitudinalRecordIndex.record_date),
            func.max(MdLongitudinalRecordIndex.record_date)
        ).where(
            MdLongitudinalRecordIndex.patient_id == patient_id
        )
        
        date_range_result = await self.db.execute(date_range_query)
        min_date, max_date = date_range_result.first()
        
        # Get recent records
        recent_query = select(MdLongitudinalRecordIndex).where(
            MdLongitudinalRecordIndex.patient_id == patient_id
        ).order_by(desc(MdLongitudinalRecordIndex.record_date)).limit(10)
        
        recent_result = await self.db.execute(recent_query)
        recent_records = recent_result.scalars().all()
        
        return {
            "patient_id": str(patient_id),
            "type_counts": type_counts,
            "date_range": {
                "earliest": min_date.isoformat() if min_date else None,
                "latest": max_date.isoformat() if max_date else None
            },
            "total_records": sum(type_counts.values()),
            "recent_records_count": len(recent_records),
            "recent_records": [
                {
                    "record_type": r.record_type,
                    "record_date": r.record_date.isoformat(),
                    "tags": r.tags
                }
                for r in recent_records
            ]
        }
