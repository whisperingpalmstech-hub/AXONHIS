import uuid
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.database import Base

class DrugContraindication(Base):
    __tablename__ = "drug_contraindications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_id = Column(String(100), nullable=False) # Refers to actual drug
    contraindicated_condition = Column(String(200), nullable=False) # e.g. severe kidney disease
    risk_description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
