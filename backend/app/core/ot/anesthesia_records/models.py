import uuid
from datetime import datetime, timezone
from enum import StrEnum
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AnesthesiaType(StrEnum):
    GENERAL = "general"
    REGIONAL = "regional"
    LOCAL = "local"
    SEDATION = "sedation"


class AnesthesiaRecord(Base):
    __tablename__ = "anesthesia_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("surgery_schedule.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    anesthesia_type: Mapped[str] = mapped_column(String(50), nullable=False)
    anesthesia_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    anesthesia_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    anesthesiologist_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    schedule = relationship("SurgerySchedule", back_populates="anesthesia_record")
    anesthesiologist = relationship("User")

    def __repr__(self) -> str:
        return f"<AnesthesiaRecord schedule_id={self.schedule_id} anesthesia_type={self.anesthesia_type}>"
