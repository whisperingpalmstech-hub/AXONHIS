import uuid
from typing import Optional
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.database import Base

class DrugClass(Base):
    __tablename__ = "drug_classes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_id = Column(String(100), nullable=False) # Refers to actual drug
    drug_class = Column(String(100), nullable=False) # e.g. beta-lactam
    therapeutic_group = Column(String(100), nullable=False) # e.g. NSAID
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
