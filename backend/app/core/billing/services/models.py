import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class BillingService(Base):
    __tablename__ = "billing_services"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_code = Column(String(50), unique=True, nullable=False, index=True)
    service_name = Column(String(255), nullable=False)
    service_category = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
