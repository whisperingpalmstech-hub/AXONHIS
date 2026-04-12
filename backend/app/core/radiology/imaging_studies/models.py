import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class ImagingStudy(Base):
    __tablename__ = "imaging_studies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_uid: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    imaging_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("imaging_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    modality: Mapped[str] = mapped_column(String(50), nullable=False)
    machine_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    study_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    study_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled") # scheduled, scanning, completed, reported

    # Relationships
    imaging_order: Mapped["ImagingOrder"] = relationship("ImagingOrder", lazy="joined")
