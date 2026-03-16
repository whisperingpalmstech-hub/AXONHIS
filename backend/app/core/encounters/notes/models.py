import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class EncounterNote(Base):
    __tablename__ = "encounter_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), nullable=False)
    note_type = Column(String(100), nullable=False) # doctor_note, nurse_note, progress_note, discharge_note
    content = Column(Text, nullable=False) # Markdown
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    encounter = relationship("Encounter", back_populates="notes")
    author = relationship("User")
