"""
AXONHIS Linen and Laundry Management Models.

Tracks hospital linen inventory, ward distribution, dirty linen collection,
washing cycles, return tracking, and utilization analytics.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer, Date, Text, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base

class LinenStatus(str, enum.Enum):
    CLEAN = "clean"
    IN_USE = "in_use"
    DIRTY_COLLECTED = "dirty_collected"
    IN_WASH = "in_wash"
    DAMAGED = "damaged"
    CONDEMNED = "condemned"

class TransactionType(str, enum.Enum):
    ISSUE_TO_WARD = "issue_to_ward"
    COLLECT_FROM_WARD = "collect_from_ward"
    SEND_TO_LAUNDRY = "send_to_laundry"
    RECEIVE_FROM_LAUNDRY = "receive_from_laundry"
    CONDEMN = "condemn"
    NEW_STOCK = "new_stock"

class LinenCategory(Base):
    __tablename__ = "linen_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True) # e.g., 'Bedsheet', 'Pillow Cover', 'Surgical Gown'
    description = Column(Text, nullable=True)
    expected_lifespan_washes = Column(Integer, default=100) # How many washes before condemnation
    is_active = Column(Boolean, default=True)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True) # Multi-tenant
    created_at = Column(DateTime, default=datetime.utcnow)

class LinenInventoryLedger(Base):
    """Tracks aggregate stock levels per department/ward"""
    __tablename__ = "linen_inventory_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("linen_categories.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(String(50), nullable=False, index=True) # E.g., 'WARD-ICU', 'CSSD-MAIN' or 'LAUNDRY-MAIN'
    
    clean_quantity = Column(Integer, default=0, nullable=False)
    dirty_quantity = Column(Integer, default=0, nullable=False)
    in_wash_quantity = Column(Integer, default=0, nullable=False)
    
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("LinenCategory")

class LaundryBatch(Base):
    """Tracks a batch of dirty linen being washed"""
    __tablename__ = "laundry_batches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_number = Column(String(50), unique=True, nullable=False, index=True)
    washer_machine_id = Column(String(50), nullable=True)
    operator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(String(20), default="washing") # 'washing', 'drying', 'ironing', 'completed'
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    total_weight_kg = Column(Numeric(6, 2), nullable=True)
    notes = Column(Text, nullable=True)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class LinenTransaction(Base):
    __tablename__ = "linen_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("linen_categories.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    
    source_department = Column(String(50), nullable=True)     # Where it came from
    destination_department = Column(String(50), nullable=True) # Where it is going
    
    batch_id = Column(UUID(as_uuid=True), ForeignKey("laundry_batches.id"), nullable=True)
    
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    transaction_date = Column(DateTime, default=datetime.utcnow, index=True)
    notes = Column(Text, nullable=True)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    category = relationship("LinenCategory")
