import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class RadiologyPriority(StrEnum):
    ROUTINE = "routine"
    URGENT = "urgent"
    STAT = "stat"

class ImagingOrderStatus(StrEnum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ImagingModality(StrEnum):
    XRAY = "X-ray"
    CT = "CT"
    MRI = "MRI"
    ULTRASOUND = "Ultrasound"
    FLUOROSCOPY = "Fluoroscopy"
    MAMMOGRAPHY = "Mammography"

class ImagingOrder(Base):
    __tablename__ = "imaging_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    encounter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    requested_modality: Mapped[str] = mapped_column(String(50), nullable=False)
    requested_study: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default=RadiologyPriority.ROUTINE)
    status: Mapped[str] = mapped_column(String(20), default=ImagingOrderStatus.PENDING)
    
    ordered_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    order: Mapped["Order"] = relationship("Order", lazy="joined")
    # scheduling: Mapped["ImagingSchedule"] = relationship("ImagingSchedule", back_populates="imaging_order", uselist=False)
