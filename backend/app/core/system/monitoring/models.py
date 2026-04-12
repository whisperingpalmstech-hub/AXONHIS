import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class TrackedError(Base):
    __tablename__ = "tracked_errors"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    error_type: Mapped[str] = mapped_column(String(100), index=True) # database, api, background_job, ai_inference
    message: Mapped[str] = mapped_column(Text)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_context: Mapped[str | None] = mapped_column(String(255), nullable=True)
    request_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    metric_type: Mapped[str] = mapped_column(String(100), index=True) # api_response, db_query, background_job, ai_inference
    endpoint_or_task: Mapped[str] = mapped_column(String(255), index=True)
    duration_ms: Mapped[float] = mapped_column(Float)
    metadata_context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
