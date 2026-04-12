import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class DiscountRule(Base):
    __tablename__ = "discount_rules"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name = Column(String(200), nullable=False)
    discount_type = Column(String(50), nullable=False)  # percentage, fixed
    discount_value = Column(Numeric(12, 2), nullable=False)
    conditions = Column(JSON, nullable=True)
