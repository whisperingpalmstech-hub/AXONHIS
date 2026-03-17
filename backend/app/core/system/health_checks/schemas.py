from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class HealthCheckOut(BaseModel):
    status: str
    timestamp: datetime
    api_status: str
    database_status: str
    redis_status: str
    ai_service_status: str
    details: Optional[Dict[str, Any]] = None

class SystemMetricsOut(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_requests: int
    queue_backlog: int

class SystemVersionOut(BaseModel):
    version: str
    environment: str
    last_deployment: datetime
