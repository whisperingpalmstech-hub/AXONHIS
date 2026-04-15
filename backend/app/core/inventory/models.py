from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
from app.database import Base

class Store(Base):
    __tablename__ = "inv_stores"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    store_type = Column(String(50), nullable=False) # 'MAIN', 'PHARMACY', 'LAB', 'WARD', 'ICU', 'OT'
    parent_store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id"), nullable=True)
    is_active = Column(Boolean, default=True)

class InvItem(Base):
    """Catalog of products available across the enterprise."""
    __tablename__ = "inv_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_code = Column(String(50), unique=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(50))
    uom = Column(String(20))
    hsn_code = Column(String(20), nullable=True)
    gst_percentage = Column(Numeric(5, 2), default=0.0)
    reorder_level = Column(Numeric(12, 2), default=0.0)
    is_approved = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

class BatchRecord(Base):
    __tablename__ = "inv_batch_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_number = Column(String(100), nullable=False, index=True)
    expiry_date = Column(DateTime(timezone=True), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False, default=0)
    purchase_price = Column(Numeric(12, 2), nullable=False, default=0)
    
    store = relationship("Store")
    item = relationship("InvItem")

class StockLedger(Base):
    __tablename__ = "inv_stock_ledger"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id", ondelete="CASCADE"), nullable=False)
    batch_record_id = Column(UUID(as_uuid=True), ForeignKey("inv_batch_records.id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    quantity_change = Column(Numeric(12, 2), nullable=False)
    closing_balance = Column(Numeric(12, 2), nullable=False) 
    reference_id = Column(String(100), nullable=True)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    item = relationship("InvItem")
    store = relationship("Store")
    batch = relationship("BatchRecord")

class StoreIndent(Base):
    __tablename__ = "inv_store_indents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indent_number = Column(String(50), unique=True, index=True)
    requesting_store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id"), nullable=False)
    issuing_store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id"), nullable=False)
    status = Column(String(50), nullable=False, default="DRAFT")
    justification = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    requesting_store = relationship("Store", foreign_keys=[requesting_store_id])
    issuing_store = relationship("Store", foreign_keys=[issuing_store_id])
    items = relationship("StoreIndentItem", back_populates="indent")

class StoreIndentItem(Base):
    __tablename__ = "inv_store_indent_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indent_id = Column(UUID(as_uuid=True), ForeignKey("inv_store_indents.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id"), nullable=False)
    requested_quantity = Column(Numeric(12, 2), nullable=False)
    approved_quantity = Column(Numeric(12, 2), nullable=True)
    issued_quantity = Column(Numeric(12, 2), default=0)

    indent = relationship("StoreIndent", back_populates="items")
    item = relationship("InvItem")

class MaterialIssue(Base):
    __tablename__ = "inv_material_issues"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_number = Column(String(50), unique=True, index=True)
    indent_id = Column(UUID(as_uuid=True), ForeignKey("inv_store_indents.id"), nullable=True)
    issuing_store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id"), nullable=False)
    receiving_store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id"), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING_ACCEPTANCE")
    issued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    issued_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    issuing_store = relationship("Store", foreign_keys=[issuing_store_id])
    receiving_store = relationship("Store", foreign_keys=[receiving_store_id])
    items = relationship("MaterialIssueItem", back_populates="issue")

class MaterialIssueItem(Base):
    __tablename__ = "inv_material_issue_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("inv_material_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id"), nullable=False)
    batch_record_id = Column(UUID(as_uuid=True), ForeignKey("inv_batch_records.id"), nullable=False)
    issued_quantity = Column(Numeric(12, 2), nullable=False)
    accepted_quantity = Column(Numeric(12, 2), nullable=True)

    issue = relationship("MaterialIssue", back_populates="items")
    item = relationship("InvItem")
    batch = relationship("BatchRecord")

class StockAdjustment(Base):
    __tablename__ = "inv_stock_adjustments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id"), nullable=False)
    batch_record_id = Column(UUID(as_uuid=True), ForeignKey("inv_batch_records.id"), nullable=False)
    system_quantity = Column(Numeric(12, 2), nullable=False)
    physical_quantity = Column(Numeric(12, 2), nullable=False)
    variance = Column(Numeric(12, 2), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING_APPROVAL")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    store = relationship("Store")
    batch = relationship("BatchRecord")

class ScrapRequest(Base):
    __tablename__ = "inv_scrap_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id"), nullable=False)
    batch_record_id = Column(UUID(as_uuid=True), ForeignKey("inv_batch_records.id"), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING_APPROVAL")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    store = relationship("Store")
    batch = relationship("BatchRecord")
class GatePass(Base):
    __tablename__ = "inv_gate_passes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pass_number = Column(String(50), unique=True)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("inv_material_issues.id"))
    carrier_name = Column(String(100))
    vehicle_number = Column(String(50))
    security_clearance_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

    issue = relationship("MaterialIssue")
    cleared_by = relationship("User")
