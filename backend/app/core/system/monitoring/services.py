import traceback
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import TrackedError, PerformanceMetric

class MonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_error(self, error_type: str, message: str, exc: Optional[Exception] = None, 
                        user_context: Optional[str] = None, request_payload: Optional[Dict[str, Any]] = None) -> TrackedError:
        stack_trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)) if exc else None
        
        tracked = TrackedError(
            error_type=error_type,
            message=message,
            stack_trace=stack_trace,
            user_context=user_context,
            request_payload=request_payload
        )
        self.db.add(tracked)
        await self.db.flush()
        return tracked

    async def get_errors(self, limit: int = 100, skip: int = 0):
        result = await self.db.execute(
            select(TrackedError).order_by(TrackedError.timestamp.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def log_performance(self, metric_type: str, endpoint_or_task: str, duration_ms: float, metadata_context: Optional[dict] = None) -> PerformanceMetric:
        perf = PerformanceMetric(
            metric_type=metric_type,
            endpoint_or_task=endpoint_or_task,
            duration_ms=duration_ms,
            metadata_context=metadata_context
        )
        self.db.add(perf)
        await self.db.flush()
        return perf

    async def get_performance_metrics(self, limit: int = 100, skip: int = 0):
        result = await self.db.execute(
            select(PerformanceMetric).order_by(PerformanceMetric.timestamp.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
