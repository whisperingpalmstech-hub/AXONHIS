import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Medication(Base):
    __tablename__ = "medications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_code = Column(String(50), nullable=False, unique=True, index=True)
    drug_name = Column(String(200), nullable=False)
    generic_name = Column(String(200), nullable=False)
    drug_class = Column(String(100), nullable=True)
    form = Column(String(50), nullable=True)
    strength = Column(String(50), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
