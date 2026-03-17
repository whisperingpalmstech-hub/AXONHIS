from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class LogCreate(BaseModel):
    level: str
    service_name: str
    message: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class LogOut(LogCreate):
    id: uuid.UUID
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)
