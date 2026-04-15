import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class PharmacyWalkInSale(Base):
    __tablename__ = "pharmacy_walkin_sales"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)
    walkin_name = Column(String(200), nullable=True)
    walkin_mobile = Column(String(20), nullable=True)
    walkin_age = Column(String(10), nullable=True)
    walkin_gender = Column(String(20), nullable=True)
    walkin_address = Column(String(500), nullable=True)
    prescriber_name = Column(String(200), nullable=True)
    pharmacist_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    net_amount = Column(Numeric(12, 2), nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="pending")  # pending, completed, cancelled

    items = relationship("PharmacySaleItem", back_populates="sale", cascade="all, delete-orphan")
    payment = relationship("PharmacySalePayment", back_populates="sale", uselist=False, cascade="all, delete-orphan")

class PharmacySaleItem(Base):
    __tablename__ = "pharmacy_sales_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_walkin_sales.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_id = Column(UUID(as_uuid=True), ForeignKey("medications.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("drug_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    dosage_instructions = Column(String(500), nullable=True)
    substituted_for_id = Column(UUID(as_uuid=True), ForeignKey("medications.id", ondelete="SET NULL"), nullable=True)

    sale = relationship("PharmacyWalkInSale", back_populates="items")

class PharmacySalePayment(Base):
    __tablename__ = "pharmacy_sales_payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_walkin_sales.id", ondelete="CASCADE"), nullable=False, unique=True)
    payment_mode = Column(String(50), nullable=False)  # Cash, Card, UPI, Net Banking
    amount_paid = Column(Numeric(12, 2), nullable=False)
    transaction_ref = Column(String(100), nullable=True)
    payment_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    sale = relationship("PharmacyWalkInSale", back_populates="payment")

class PharmacyPrescriptionUpload(Base):
    __tablename__ = "pharmacy_prescriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_walkin_sales.id", ondelete="CASCADE"), nullable=True, index=True)
    file_url = Column(String(500), nullable=False)
    extracted_text = Column(Text, nullable=True)
    doctor_name = Column(String(200), nullable=True)
    requires_validation = Column(Boolean, default=True)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

class PharmacySalesAuditLog(Base):
    __tablename__ = "pharmacy_sales_audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    pharmacist_id = Column(UUID(as_uuid=True), nullable=False)
    action_type = Column(String(100), nullable=False)  # e.g., SALE_COMPLETED, SALE_CANCELLED
    details = Column(JSONB, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
