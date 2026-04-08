from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Individual component health status."""
    name: str
    status: HealthStatus
    response_time_ms: Optional[float] = None
    message: Optional[str] = None
    last_check: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthCheckOut(BaseModel):
    """Machine-readable health check response."""
    status: HealthStatus
    timestamp: datetime
    version: str
    environment: str
    uptime_seconds: float
    components: Dict[str, ComponentHealth]
    checks_passed: int
    checks_failed: int
    total_checks: int
    # Legacy fields for backward compatibility
    api_status: str = None
    database_status: str = None
    redis_status: str = None
    ai_service_status: str = None
    details: Optional[Dict[str, Any]] = None


class SystemMetricsOut(BaseModel):
    """System metrics for monitoring."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int
    active_requests: int
    queue_backlog: int
    database_connections: int
    cache_hit_rate: Optional[float] = None
    timestamp: datetime


class SystemVersionOut(BaseModel):
    """System version information."""
    version: str
    git_commit: Optional[str] = None
    build_date: Optional[datetime] = None
    environment: str
    last_deployment: datetime
    api_version: str


class ReadinessCheck(BaseModel):
    """Readiness check for Kubernetes/liveness probes."""
    ready: bool
    timestamp: datetime
    checks: Dict[str, bool]


class LivenessCheck(BaseModel):
    """Liveness check for Kubernetes/liveness probes."""
    alive: bool
    timestamp: datetime
