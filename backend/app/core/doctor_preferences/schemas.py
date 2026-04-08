from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class DoctorPreferenceCreate(BaseModel):
    clinician_id: UUID
    preference_category: str
    preference_key: str
    preference_value: Any
    data_type: str
    description: Optional[str] = None
    is_system_default: bool = False


class DoctorPreferenceUpdate(BaseModel):
    preference_value: Optional[Any] = None
    description: Optional[str] = None


class DoctorPreferenceResponse(BaseModel):
    preference_id: UUID
    clinician_id: UUID
    preference_category: str
    preference_key: str
    preference_value: Any
    data_type: str
    description: Optional[str]
    is_system_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoctorPreferenceBulkUpdate(BaseModel):
    clinician_id: UUID
    preferences: Dict[str, Dict[str, Any]]  # {preference_key: {value, data_type, description}}
