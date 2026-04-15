"""Physical Stock Verification Models for Inventory."""
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Integer, Numeric, UUID
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid

from app.database import Base


class VerificationSchedule(Base):
    """Verification schedule."""
    __tablename__ = "inv_verification_schedules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_number = Column(String(100), unique=True, nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id", ondelete="CASCADE"), nullable=True, index=True)
    verification_type = Column(String(50), nullable=False)  # 'full', 'partial', 'category_based'
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False, default="scheduled")  # 'scheduled', 'in_progress', 'completed', 'cancelled'
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)


class VerificationItem(Base):
    """Items in a verification schedule."""
    __tablename__ = "inv_verification_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("inv_verification_schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id", ondelete="CASCADE"), nullable=False)
    batch_record_id = Column(UUID(as_uuid=True), ForeignKey("inv_batch_records.id", ondelete="CASCADE"), nullable=False)
    expected_quantity = Column(Numeric(12, 2), nullable=False)
    verified_quantity = Column(Numeric(12, 2), nullable=True)
    variance = Column(Numeric(12, 2), nullable=True)
    variance_reason = Column(Text, nullable=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'verified', 'discrepancy'


class Discrepancy(Base):
    """Discrepancy tracking."""
    __tablename__ = "inv_discrepancies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    verification_item_id = Column(UUID(as_uuid=True), ForeignKey("inv_verification_items.id", ondelete="CASCADE"), nullable=False, index=True)
    discrepancy_type = Column(String(50), nullable=False)  # 'shortage', 'excess', 'damage'
    expected_quantity = Column(Numeric(12, 2), nullable=False)
    actual_quantity = Column(Numeric(12, 2), nullable=False)
    variance = Column(Numeric(12, 2), nullable=False)
    value = Column(Numeric(12, 2), nullable=True)
    reason = Column(Text, nullable=True)
    resolution_status = Column(String(50), nullable=False, default="pending")  # 'pending', 'investigated', 'resolved', 'written_off'
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class VerificationReport(Base):
    """Verification report generation."""
    __tablename__ = "inv_verification_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_number = Column(String(100), unique=True, nullable=False, index=True)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("inv_verification_schedules.id", ondelete="SET NULL"), nullable=True, index=True)
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    total_items = Column(Integer, nullable=False)
    verified_items = Column(Integer, nullable=False)
    discrepancy_count = Column(Integer, nullable=False)
    total_variance = Column(Numeric(12, 2), nullable=False)
    total_variance_value = Column(Numeric(12, 2), nullable=True)
