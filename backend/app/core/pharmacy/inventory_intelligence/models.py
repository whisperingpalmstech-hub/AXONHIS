import uuid
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, DateTime, Date, Numeric, Text, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class PharmacyInventoryBatch(Base):
    __tablename__ = "pharmacy_inventory_batches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_id = Column(UUID(as_uuid=True), ForeignKey("medications.id", ondelete="RESTRICT"), nullable=False, index=True)
    store_id = Column(String(50), nullable=False, index=True) # E.g. "MAIN", "ICU", "WARD"
    batch_number = Column(String(100), nullable=False, index=True)
    expiry_date = Column(Date, nullable=False, index=True)
    available_quantity = Column(Numeric(12, 2), nullable=False, default=0.0)
    purchase_price = Column(Numeric(12, 2), nullable=False, default=0.0)
    selling_price = Column(Numeric(12, 2), nullable=False, default=0.0)

class PharmacyStockMovement(Base):
    __tablename__ = "pharmacy_stock_movements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_inventory_batches.id"), nullable=False)
    store_id = Column(String(50), nullable=False)
    transaction_type = Column(String(50), nullable=False, index=True) # PURCHASE, DISPENSE, RETURN, TRANSFER
    quantity_change = Column(Numeric(12, 2), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    reference_id = Column(String(100), nullable=True)

class PharmacyItemKit(Base):
    __tablename__ = "pharmacy_item_kits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kit_name = Column(String(150), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="ACTIVE")
    kit_components = Column(JSON, nullable=False, default=list)

class PharmacyInventoryAlert(Base):
    __tablename__ = "pharmacy_inventory_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String(50), nullable=False) # EXPIRY, REORDER, DEAD_STOCK
    drug_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_inventory_batches.id"), nullable=True)
    store_id = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    alert_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="UNRESOLVED") # UNRESOLVED, ACKNOWLEDGED, RESOLVED

class PharmacyInventoryAnalysis(Base):
    __tablename__ = "pharmacy_inventory_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_id = Column(UUID(as_uuid=True), ForeignKey("medications.id", ondelete="CASCADE"), nullable=False, unique=True)
    abc_category = Column(String(5), nullable=True) # A, B, C
    ved_category = Column(String(10), nullable=True) # VITAL, ESSENTIAL, DESIRABLE
    is_dead_stock = Column(Integer, default=0) # boolean int
    last_analyzed = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class PharmacyInventoryLog(Base):
    __tablename__ = "pharmacy_inventory_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    drug_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"), nullable=True)
    quantity_change = Column(Numeric(12, 2), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
