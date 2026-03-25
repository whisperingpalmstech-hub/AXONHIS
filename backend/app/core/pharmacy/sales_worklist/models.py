import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class PharmacySalesWorklist(Base):
    __tablename__ = "pharmacy_sales_worklist"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)
    patient_name = Column(String(200), nullable=True)
    uhid = Column(String(50), nullable=True)
    visit_id = Column(UUID(as_uuid=True), nullable=True)
    doctor_name = Column(String(200), nullable=True)
    prescription_id = Column(UUID(as_uuid=True), index=True)
    prescription_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String(50), nullable=False, default="Pending") # Pending, In Progress, Dispensed, Completed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    prescriptions = relationship("PharmacyPrescription", back_populates="worklist_item")

class PharmacyPrescription(Base):
    __tablename__ = "pharmacy_worklist_prescriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worklist_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_sales_worklist.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_id = Column(UUID(as_uuid=True), nullable=True)
    medication_name = Column(String(255), nullable=False)
    dosage_instructions = Column(String(500), nullable=True)
    quantity_prescribed = Column(Numeric(12, 2), nullable=False)
    doctor_notes = Column(Text, nullable=True)
    is_non_formulary = Column(Boolean, default=False)
    substituted_for = Column(String(255), nullable=True)

    worklist_item = relationship("PharmacySalesWorklist", back_populates="prescriptions")

class PharmacyDispensingRecord(Base):
    __tablename__ = "pharmacy_dispensing_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worklist_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_sales_worklist.id", ondelete="CASCADE"), nullable=False, index=True)
    prescription_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_worklist_prescriptions.id", ondelete="CASCADE"), nullable=False)
    drug_id = Column(UUID(as_uuid=True), nullable=True)
    medication_name = Column(String(255), nullable=False)
    quantity_dispensed = Column(Numeric(12, 2), nullable=False)
    dosage_instructions = Column(String(500), nullable=True)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0.0)
    total_price = Column(Numeric(12, 2), nullable=False, default=0.0)
    dispensed_by = Column(UUID(as_uuid=True), nullable=True)
    dispensed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    batches = relationship("PharmacyDispenseBatch", back_populates="dispensing_record", cascade="all, delete-orphan")

class PharmacyDispenseBatch(Base):
    __tablename__ = "pharmacy_dispense_batches"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispense_record_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_dispensing_records.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = Column(UUID(as_uuid=True), nullable=False) # Maps to inventory batches
    batch_number = Column(String(100), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    dispensing_record = relationship("PharmacyDispensingRecord", back_populates="batches")

class PharmacyDispenseLog(Base):
    __tablename__ = "pharmacy_dispense_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worklist_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    pharmacist_id = Column(UUID(as_uuid=True), nullable=False)
    action_type = Column(String(100), nullable=False)
    details = Column(JSONB, nullable=False)
    billing_transaction_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
