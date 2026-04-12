import uuid
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.database import Base

class DrugInteraction(Base):
    __tablename__ = "drug_interactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_a = Column(String(100), nullable=False)
    drug_b = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False) # minor, moderate, major, contraindicated
    interaction_description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
