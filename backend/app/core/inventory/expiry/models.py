"""Expiry Management Models for Inventory."""
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Integer, Numeric, UUID
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid

from app.database import Base


class ExpiryAlert(Base):
    """Expiry alert configuration."""
    __tablename__ = "inv_expiry_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String(50), nullable=False)  # 'warning', 'critical', 'expired'
    threshold_days = Column(Integer, nullable=False)  # e.g., 30 days for warning, 0 for expired
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ExpiryTracking(Base):
    """Track expiring batches."""
    __tablename__ = "inv_expiry_tracking"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_record_id = Column(UUID(as_uuid=True), ForeignKey("inv_batch_records.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id", ondelete="RESTRICT"), nullable=True, index=True)
    expiry_date = Column(DateTime(timezone=True), nullable=False, index=True)
    quantity = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), nullable=False, default="active")  # 'active', 'near_expiry', 'expired', 'consumed', 'disposed'
    alert_sent = Column(Boolean, default=False)
    alert_sent_at = Column(DateTime(timezone=True), nullable=True)
    disposal_action = Column(String(50), nullable=True)  # 'return_to_supplier', 'scrap', 'discount_sale'
    disposal_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ExpiryReport(Base):
    """Expiry report generation."""
    __tablename__ = "inv_expiry_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_number = Column(String(100), unique=True, nullable=False, index=True)
    report_type = Column(String(50), nullable=False)  # 'daily', 'weekly', 'monthly'
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    total_items = Column(Integer, nullable=False)
    near_expiry_count = Column(Integer, nullable=False)
    expired_count = Column(Integer, nullable=False)
    total_value = Column(Numeric(12, 2), nullable=False)
    expiry_value = Column(Numeric(12, 2), nullable=False)


class ReturnToSupplier(Base):
    """Return to supplier tracking."""
    __tablename__ = "inv_return_to_supplier"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    return_number = Column(String(100), unique=True, nullable=False, index=True)
    batch_record_id = Column(UUID(as_uuid=True), ForeignKey("inv_batch_records.id", ondelete="RESTRICT"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    return_quantity = Column(Numeric(12, 2), nullable=False)
    return_reason = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'approved', 'rejected', 'completed'
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class DiscountSale(Base):
    """Discount sale for expiring items."""
    __tablename__ = "inv_discount_sales"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_record_id = Column(UUID(as_uuid=True), ForeignKey("inv_batch_records.id", ondelete="RESTRICT"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id", ondelete="RESTRICT"), nullable=False)
    original_price = Column(Numeric(12, 2), nullable=False)
    discount_percentage = Column(Numeric(5, 2), nullable=False)
    discounted_price = Column(Numeric(12, 2), nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
