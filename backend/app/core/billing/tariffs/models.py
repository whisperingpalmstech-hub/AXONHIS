import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class ServiceTariff(Base):
    __tablename__ = "service_tariffs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("billing_services.id", ondelete="CASCADE"), nullable=False, index=True)
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)
