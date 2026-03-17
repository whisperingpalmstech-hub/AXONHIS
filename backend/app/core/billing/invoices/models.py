import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="RESTRICT"), nullable=False, index=True)
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), nullable=False, default="draft")  # draft, issued, paid, partially_paid, cancelled
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
