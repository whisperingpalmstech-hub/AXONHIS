import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class BillingEntry(Base):
    __tablename__ = "billing_entries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=True, index=True)
    service_id = Column(UUID(as_uuid=True), ForeignKey("billing_services.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Numeric(12, 2), nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    status = Column(String(30), nullable=False, default="pending")  # pending, charged, cancelled, reversed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class BillingReversal(Base):
    __tablename__ = "billing_reversals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_entry_id = Column(UUID(as_uuid=True), ForeignKey("billing_entries.id", ondelete="CASCADE"), nullable=False, unique=True)
    reason = Column(String(500), nullable=False)
    reversed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reversed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class FinancialAuditLog(Base):
    __tablename__ = "financial_audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String(100), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    entity_type = Column(String(50), nullable=False)  # 'billing_entry', 'invoice', 'payment'
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    details = Column(String, nullable=True)
