"""Stock Valuation Models for Inventory."""
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Integer, Numeric, UUID
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid

from app.database import Base


class StockValuation(Base):
    """Stock valuation records."""
    __tablename__ = "inv_stock_valuations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    valuation_number = Column(String(100), unique=True, nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id", ondelete="RESTRICT"), nullable=True, index=True)
    valuation_method = Column(String(50), nullable=False)  # 'fifo', 'lifo', 'moving_average', 'weighted_average'
    valuation_date = Column(DateTime(timezone=True), nullable=False, index=True)
    total_value = Column(Numeric(12, 2), nullable=False)
    total_quantity = Column(Numeric(12, 2), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class StockValuationItem(Base):
    """Individual item valuations."""
    __tablename__ = "inv_stock_valuation_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    valuation_id = Column(UUID(as_uuid=True), ForeignKey("inv_stock_valuations.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id", ondelete="RESTRICT"), nullable=False)
    batch_record_id = Column(UUID(as_uuid=True), ForeignKey("inv_batch_records.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)
    valuation_method = Column(String(50), nullable=False)


class ValuationMethod(Base):
    """Valuation method configuration."""
    __tablename__ = "inv_valuation_methods"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    method_name = Column(String(50), nullable=False, unique=True)  # 'fifo', 'lifo', 'moving_average', 'weighted_average'
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class StockAdjustment(Base):
    """Stock adjustment for valuation differences."""
    __tablename__ = "inv_stock_adjustments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    adjustment_number = Column(String(100), unique=True, nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id", ondelete="RESTRICT"), nullable=False)
    batch_record_id = Column(UUID(as_uuid=True), ForeignKey("inv_batch_records.id", ondelete="RESTRICT"), nullable=False)
    adjustment_type = Column(String(50), nullable=False)  # 'positive', 'negative'
    quantity = Column(Numeric(12, 2), nullable=False)
    reason = Column(Text, nullable=False)
    adjustment_value = Column(Numeric(12, 2), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
