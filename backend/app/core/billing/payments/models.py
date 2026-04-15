import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_method = Column(String(50), nullable=False)  # cash, card, online, insurance
    amount = Column(Numeric(12, 2), nullable=False)
    payment_status = Column(String(50), nullable=False, default="pending")  # pending, completed, failed
    payment_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
