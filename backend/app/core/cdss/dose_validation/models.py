import uuid
from typing import Optional
from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.database import Base

class DrugDosageGuideline(Base):
    __tablename__ = "drug_dosage_guidelines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_id = Column(String(100), nullable=False) # Refers to actual drug
    min_dose = Column(Float, nullable=False)
    max_dose = Column(Float, nullable=False)
    age_group = Column(String(50), nullable=True) # e.g. adult, pediatric
    weight_range = Column(String(50), nullable=True) # e.g. 50-70kg
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
