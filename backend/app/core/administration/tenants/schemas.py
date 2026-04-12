import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class SiteCreate(BaseModel):
    name: str
    site_code: str
    location_address: Optional[str] = None
    timezone: str = "UTC"
    is_active: bool = True
    site_settings: Dict[str, Any] = {}

class SiteOut(SiteCreate):
    id: uuid.UUID
    org_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OrgCreate(BaseModel):
    name: str
    org_code: str
    country: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool = True
    default_language: str = "en"
    global_settings: Dict[str, Any] = {}
    admin_password: str | None = None

class OrgOut(OrgCreate):
    id: uuid.UUID
    created_at: datetime
    sites: List[SiteOut] = []
    model_config = ConfigDict(from_attributes=True)
