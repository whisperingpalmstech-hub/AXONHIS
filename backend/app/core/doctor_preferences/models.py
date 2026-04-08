from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class MdDoctorPreference(Base):
    """
    Doctor preference model for doctor-specific UI and workflow preferences.
    """
    __tablename__ = "md_doctor_preference"

    preference_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinician_id = Column(UUID(as_uuid=True), ForeignKey("md_clinician.clinician_id", ondelete="CASCADE"), nullable=False, index=True)
    preference_category = Column(String(50), nullable=False, index=True)  # UI, WORKFLOW, NOTIFICATIONS, etc.
    preference_key = Column(String(255), nullable=False)
    preference_value = Column(JSONB, nullable=False, default={})
    data_type = Column(String(20), nullable=False)  # STRING, NUMBER, BOOLEAN, JSON
    description = Column(Text, nullable=True)
    is_system_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    clinician = relationship("MdClinician", backref="preferences")

    __table_args__ = (
        Index('idx_doctor_pref_clinician', 'clinician_id', 'preference_category'),
        Index('idx_doctor_pref_key', 'preference_key'),
    )
