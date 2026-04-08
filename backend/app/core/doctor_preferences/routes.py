from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.doctor_preferences.schemas import (
    DoctorPreferenceCreate,
    DoctorPreferenceUpdate,
    DoctorPreferenceResponse,
    DoctorPreferenceBulkUpdate
)
from app.core.doctor_preferences.services import DoctorPreferenceService
from app.database import get_db

router = APIRouter(prefix="/doctor-preferences", tags=["doctor-preferences"])


@router.post("/preferences", response_model=DoctorPreferenceResponse)
async def set_preference(
    preference_data: DoctorPreferenceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Set a doctor preference (create or update)."""
    service = DoctorPreferenceService(db)
    preference = await service.set_preference(preference_data)
    return preference


@router.get("/clinicians/{clinician_id}/preferences/{preference_key}", response_model=DoctorPreferenceResponse)
async def get_preference(
    clinician_id: UUID,
    preference_key: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific doctor preference."""
    service = DoctorPreferenceService(db)
    preference = await service.get_preference(clinician_id, preference_key)
    if not preference:
        raise HTTPException(status_code=404, detail="Preference not found")
    return preference


@router.get("/clinicians/{clinician_id}/preferences/{preference_key}/value")
async def get_preference_value(
    clinician_id: UUID,
    preference_key: str,
    default: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get preference value with fallback to default."""
    service = DoctorPreferenceService(db)
    value = await service.get_preference_value(clinician_id, preference_key, default)
    return {"preference_key": preference_key, "value": value}


@router.get("/clinicians/{clinician_id}/preferences", response_model=List[DoctorPreferenceResponse])
async def get_all_preferences(
    clinician_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all preferences for a clinician."""
    service = DoctorPreferenceService(db)
    preferences = await service.get_all_preferences(clinician_id)
    return preferences


@router.get("/clinicians/{clinician_id}/preferences/category/{preference_category}", response_model=List[DoctorPreferenceResponse])
async def get_preferences_by_category(
    clinician_id: UUID,
    preference_category: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all preferences for a clinician in a category."""
    service = DoctorPreferenceService(db)
    preferences = await service.get_preferences_by_category(clinician_id, preference_category)
    return preferences


@router.post("/preferences/bulk")
async def bulk_update_preferences(
    bulk_data: DoctorPreferenceBulkUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Bulk update preferences for a clinician."""
    service = DoctorPreferenceService(db)
    preferences = await service.bulk_update_preferences(bulk_data)
    return {"message": f"Updated {len(preferences)} preferences"}


@router.delete("/clinicians/{clinician_id}/preferences/{preference_key}")
async def delete_preference(
    clinician_id: UUID,
    preference_key: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a doctor preference."""
    service = DoctorPreferenceService(db)
    success = await service.delete_preference(clinician_id, preference_key)
    if not success:
        raise HTTPException(status_code=404, detail="Preference not found")
    return {"message": "Preference deleted successfully"}


@router.post("/clinicians/{clinician_id}/reset")
async def reset_to_defaults(
    clinician_id: UUID,
    preference_category: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Reset preferences to system defaults for a clinician."""
    service = DoctorPreferenceService(db)
    count = await service.reset_to_defaults(clinician_id, preference_category)
    return {"message": f"Reset {count} preferences to defaults"}
