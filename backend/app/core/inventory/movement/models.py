"""Stock Movement Analytics Models for Inventory."""
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Integer, Numeric, UUID
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid

from app.database import Base


class StockTransfer(Base):
    """Inter-store transfer tracking."""
    __tablename__ = "inv_stock_transfers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transfer_number = Column(String(100), unique=True, nullable=False, index=True)
    from_store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id", ondelete="CASCADE"), nullable=False, index=True)
    to_store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id", ondelete="CASCADE"), nullable=False, index=True)
    indent_id = Column(UUID(as_uuid=True), ForeignKey("inv_store_indents.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'approved', 'in_transit', 'received', 'rejected', 'cancelled'
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    received_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class StockTransferItem(Base):
    """Items in a stock transfer."""
    __tablename__ = "inv_stock_transfer_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transfer_id = Column(UUID(as_uuid=True), ForeignKey("inv_stock_transfers.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id", ondelete="CASCADE"), nullable=False)
    batch_record_id = Column(UUID(as_uuid=True), ForeignKey("inv_batch_records.id", ondelete="CASCADE"), nullable=False)
    requested_quantity = Column(Numeric(12, 2), nullable=False)
    approved_quantity = Column(Numeric(12, 2), nullable=True)
    shipped_quantity = Column(Numeric(12, 2), nullable=False, default=0)
    received_quantity = Column(Numeric(12, 2), nullable=False, default=0)
    variance = Column(Numeric(12, 2), nullable=True)
    reason = Column(Text, nullable=True)


class MovementReport(Base):
    """Movement reports."""
    __tablename__ = "inv_movement_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_type = Column(String(50), nullable=False)  # 'inter_store', 'receipt', 'issue', 'consumption'
    from_store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id", ondelete="SET NULL"), nullable=True)
    to_store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id", ondelete="SET NULL"), nullable=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id", ondelete="CASCADE"), nullable=False)
    batch_record_id = Column(UUID(as_uuid=True), ForeignKey("inv_batch_records.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    movement_date = Column(DateTime(timezone=True), nullable=False)
    reference_type = Column(String(50), nullable=True)  # 'indent', 'issue', 'adjustment', 'scrap'
    reference_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class TransferApproval(Base):
    """Transfer approval workflow."""
    __tablename__ = "inv_transfer_approvals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transfer_id = Column(UUID(as_uuid=True), ForeignKey("inv_stock_transfers.id", ondelete="CASCADE"), nullable=False, index=True)
    approval_level = Column(Integer, nullable=False)  # 1, 2, 3 for multi-level approval
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'approved', 'rejected'
    comments = Column(Text, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
