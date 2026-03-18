import uuid
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.database import Base

class CDSSAlert(Base):
    __tablename__ = "cdss_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    alert_type = Column(String(50), nullable=False) # interaction, allergy, dosage, duplicate, contraindication
    severity = Column(String(50), nullable=False) # info, warning, critical
    message = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=True)
    is_overridden = Column(Boolean, default=False)
    overridden_by = Column(UUID(as_uuid=True), nullable=True) # User ID who overrode
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
