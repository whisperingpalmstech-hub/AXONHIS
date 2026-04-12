import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BloodComponent(Base):
    __tablename__ = "blood_components"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    component_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    storage_temperature: Mapped[str] = mapped_column(String(50), nullable=False)
    shelf_life_days: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
