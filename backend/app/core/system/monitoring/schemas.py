from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class TrackedErrorOut(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    error_type: str
    message: str
    stack_trace: Optional[str] = None
    user_context: Optional[str] = None
    request_payload: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

class PerformanceMetricOut(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    metric_type: str
    endpoint_or_task: str
    duration_ms: float
    metadata_context: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)
