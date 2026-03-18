import uuid
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.database import Base

class DrugAllergyMapping(Base):
    __tablename__ = "drug_allergy_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    allergy_type = Column(String(100), nullable=False) # e.g. penicillin
    drug_class = Column(String(100), nullable=False) # e.g. beta-lactam
    reaction_risk = Column(String(50), nullable=False) # e.g. severe
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
