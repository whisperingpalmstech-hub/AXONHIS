from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.core.doctor_preferences.models import MdDoctorPreference
from app.core.doctor_preferences.schemas import (
    DoctorPreferenceCreate,
    DoctorPreferenceUpdate,
    DoctorPreferenceBulkUpdate
)


class DoctorPreferenceService:
    """Service for managing doctor-specific preferences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def set_preference(
        self,
        preference_data: DoctorPreferenceCreate
    ) -> MdDoctorPreference:
        """Set a doctor preference (create or update)."""
        # Check if preference already exists
        query = select(MdDoctorPreference).where(
            and_(
                MdDoctorPreference.clinician_id == preference_data.clinician_id,
                MdDoctorPreference.preference_key == preference_data.preference_key
            )
        )
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            existing.preference_value = preference_data.preference_value
            existing.data_type = preference_data.data_type
            existing.description = preference_data.description
            existing.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new
            preference = MdDoctorPreference(
                clinician_id=preference_data.clinician_id,
                preference_category=preference_data.preference_category,
                preference_key=preference_data.preference_key,
                preference_value=preference_data.preference_value,
                data_type=preference_data.data_type,
                description=preference_data.description,
                is_system_default=preference_data.is_system_default
            )
            self.db.add(preference)
            await self.db.commit()
            await self.db.refresh(preference)
            return preference

    async def get_preference(
        self,
        clinician_id: uuid.UUID,
        preference_key: str
    ) -> Optional[MdDoctorPreference]:
        """Get a specific doctor preference."""
        query = select(MdDoctorPreference).where(
            and_(
                MdDoctorPreference.clinician_id == clinician_id,
                MdDoctorPreference.preference_key == preference_key
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_preference_value(
        self,
        clinician_id: uuid.UUID,
        preference_key: str,
        default: Any = None
    ) -> Any:
        """Get preference value with fallback to default."""
        preference = await self.get_preference(clinician_id, preference_key)
        if preference:
            return preference.preference_value
        return default

    async def get_preferences_by_category(
        self,
        clinician_id: uuid.UUID,
        preference_category: str
    ) -> List[MdDoctorPreference]:
        """Get all preferences for a clinician in a category."""
        query = select(MdDoctorPreference).where(
            and_(
                MdDoctorPreference.clinician_id == clinician_id,
                MdDoctorPreference.preference_category == preference_category
            )
        ).order_by(MdDoctorPreference.preference_key)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all_preferences(
        self,
        clinician_id: uuid.UUID
    ) -> List[MdDoctorPreference]:
        """Get all preferences for a clinician."""
        query = select(MdDoctorPreference).where(
            MdDoctorPreference.clinician_id == clinician_id
        ).order_by(MdDoctorPreference.preference_category, MdDoctorPreference.preference_key)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def bulk_update_preferences(
        self,
        bulk_data: DoctorPreferenceBulkUpdate
    ) -> List[MdDoctorPreference]:
        """Bulk update preferences for a clinician."""
        updated_preferences = []
        
        for pref_key, pref_data in bulk_data.preferences.items():
            preference = await self.set_preference(
                DoctorPreferenceCreate(
                    clinician_id=bulk_data.clinician_id,
                    preference_category=pref_data.get("category", "GENERAL"),
                    preference_key=pref_key,
                    preference_value=pref_data.get("value"),
                    data_type=pref_data.get("data_type", "JSON"),
                    description=pref_data.get("description")
                )
            )
            updated_preferences.append(preference)
        
        return updated_preferences

    async def delete_preference(
        self,
        clinician_id: uuid.UUID,
        preference_key: str
    ) -> bool:
        """Delete a doctor preference."""
        query = select(MdDoctorPreference).where(
            and_(
                MdDoctorPreference.clinician_id == clinician_id,
                MdDoctorPreference.preference_key == preference_key
            )
        )
        result = await self.db.execute(query)
        preference = result.scalar_one_or_none()
        
        if not preference:
            return False
        
        await self.db.delete(preference)
        await self.db.commit()
        return True

    async def reset_to_defaults(
        self,
        clinician_id: uuid.UUID,
        preference_category: Optional[str] = None
    ) -> int:
        """Reset preferences to system defaults for a clinician."""
        conditions = [
            MdDoctorPreference.clinician_id == clinician_id,
            MdDoctorPreference.is_system_default == False
        ]
        
        if preference_category:
            conditions.append(MdDoctorPreference.preference_category == preference_category)
        
        query = select(MdDoctorPreference).where(and_(*conditions))
        result = await self.db.execute(query)
        preferences = result.scalars().all()
        
        count = 0
        for pref in preferences:
            await self.db.delete(pref)
            count += 1
        
        await self.db.commit()
        return count
