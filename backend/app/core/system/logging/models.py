import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    level: Mapped[str] = mapped_column(String(50), index=True) # INFO, WARNING, ERROR, CRITICAL
    service_name: Mapped[str] = mapped_column(String(100), index=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    message: Mapped[str] = mapped_column(Text)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
