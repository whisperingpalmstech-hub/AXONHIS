import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base

class EncounterTimeline(Base):
    __tablename__ = "encounter_timeline"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), nullable=False)
    event_type = Column(String(100), nullable=False) # consultation_started, vitals_recorded
    event_time = Column(DateTime(timezone=True), default=datetime.utcnow)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    description = Column(String(500), nullable=True)
    metadata_json = Column(JSONB, nullable=True)

    encounter = relationship("Encounter", back_populates="timeline_events")
    actor = relationship("User")
