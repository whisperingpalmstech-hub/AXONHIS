import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, JSON, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class PharmacyNarcoticsOrder(Base):
    __tablename__ = "pharmacy_narcotics_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    patient_name = Column(String(255), nullable=False)
    uhid = Column(String(100), index=True, nullable=False)
    admission_number = Column(String(100), index=True, nullable=False)
    ward = Column(String(100), nullable=True)
    bed_number = Column(String(100), nullable=True)
    prescribing_doctor = Column(String(200), nullable=False)
    
    drug_id = Column(UUID(as_uuid=True), nullable=True)
    medication_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=True)
    requested_quantity = Column(Numeric(10, 2), nullable=False)
    
    order_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String(50), default="Pending Validation") # Pending Validation, Approved, Rejected, Dispensed, Delivered
    
    is_narcotics = Column(Boolean, default=True)
    
    # Validation
    validated_by = Column(UUID(as_uuid=True), nullable=True) # Pharmacist In-Charge
    validation_date = Column(DateTime(timezone=True), nullable=True)
    validation_remarks = Column(Text, nullable=True)
    
    # Delivery
    nurse_name = Column(String(200), nullable=True)
    delivery_time = Column(DateTime(timezone=True), nullable=True)
    handover_notes = Column(Text, nullable=True)
    
    dispenses = relationship("PharmacyNarcoticsDispense", back_populates="order", cascade="all, delete-orphan")
    returns = relationship("PharmacyNarcoticsAmpouleReturn", back_populates="order", cascade="all, delete-orphan")
    logs = relationship("PharmacyNarcoticsAuditLog", back_populates="order", cascade="all, delete-orphan")

class PharmacyNarcoticsDispense(Base):
    __tablename__ = "pharmacy_narcotics_dispense"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_narcotics_orders.id"), nullable=False, index=True)
    batch_id = Column(UUID(as_uuid=True), nullable=True)
    batch_number = Column(String(100), nullable=False)
    dispensed_quantity = Column(Numeric(10, 2), nullable=False)
    dispensing_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    dispensed_by = Column(UUID(as_uuid=True), nullable=True)
    
    order = relationship("PharmacyNarcoticsOrder", back_populates="dispenses")

class PharmacyNarcoticsAmpouleReturn(Base):
    __tablename__ = "pharmacy_narcotics_ampoule_returns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_narcotics_orders.id"), nullable=False, index=True)
    dispense_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_narcotics_dispense.id"), nullable=True)
    
    medication_name = Column(String(255), nullable=False)
    returned_quantity = Column(Numeric(10, 2), nullable=False)
    returned_by_nurse = Column(String(200), nullable=False)
    return_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    verified_by_pharmacist = Column(UUID(as_uuid=True), nullable=True)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    
    order = relationship("PharmacyNarcoticsOrder", back_populates="returns")

class PharmacyNarcoticsInventory(Base):
    __tablename__ = "pharmacy_narcotics_inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    medication_name = Column(String(255), nullable=False)
    batch_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    batch_number = Column(String(100), nullable=False)
    stock_quantity = Column(Numeric(12, 2), nullable=False, default=0)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PharmacyNarcoticsAuditLog(Base):
    __tablename__ = "pharmacy_narcotics_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_narcotics_orders.id"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True) # Could be String for Nurse
    action_type = Column(String(100), nullable=False) # Created, Validated, Dispensed, Delivered, Ampoule Returned, Verified
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    order = relationship("PharmacyNarcoticsOrder", back_populates="logs")
