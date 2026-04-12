import uuid
from datetime import datetime, timezone
from enum import StrEnum
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SurgeryNoteType(StrEnum):
    OPERATIVE_NOTE = "operative_note"
    PROCEDURE_SUMMARY = "procedure_summary"
    COMPLICATION_NOTE = "complication_note"


class SurgeryNote(Base):
    __tablename__ = "surgery_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("surgery_schedule.id", ondelete="CASCADE"), nullable=False, index=True
    )
    note_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    schedule = relationship("SurgerySchedule", back_populates="notes")
    author = relationship("User")

    def __repr__(self) -> str:
        return f"<SurgeryNote schedule_id={self.schedule_id} note_type={self.note_type}>"
