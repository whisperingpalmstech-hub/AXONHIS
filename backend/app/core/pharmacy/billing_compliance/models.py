import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class PharmacyBillingRecord(Base):
    __tablename__ = "pharmacy_billing_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    patient_id = Column(UUID(as_uuid=True), index=True, nullable=True) # Maps to global patient UHID
    encounter_id = Column(UUID(as_uuid=True), index=True, nullable=True) # If tied to an active IP/OP encounter
    bill_number = Column(String, unique=True, index=True)
    billing_type = Column(String, index=True) # "OP_WALKIN", "OP_PRESCRIPTION", "IP_DISCHARGE"
    
    total_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    net_payable = Column(Float, default=0.0)
    
    payment_status = Column(String, default="PENDING", index=True) # PENDING, PARTIAL, PAID, REFUNDED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True)) # Staff ID

    # N:1 composition items stored as JSON array of {"drug_id", "qty", "unit_price", "tax"}
    bill_items = Column(JSON, default=list)

class PharmacyDiscountRecord(Base):
    __tablename__ = "pharmacy_discount_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_billing_records.id"), index=True)
    discount_type = Column(String) # HOSPITAL, DOCTOR, STAFF, PROMO
    discount_mode = Column(String) # PERCENTAGE, FIXED
    discount_value = Column(Float)
    approved_amount = Column(Float)
    
    authorized_by = Column(UUID(as_uuid=True), nullable=True) # Supervisor ID
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PharmacyPaymentTransaction(Base):
    __tablename__ = "pharmacy_payment_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_billing_records.id"), index=True)
    receipt_number = Column(String, unique=True, index=True)
    
    amount_paid = Column(Float)
    payment_mode = Column(String) # CASH, CREDIT_CARD, UPI, INSURANCE
    transaction_reference = Column(String, nullable=True) # Bank Txn ID or Insurance Claim Num
    
    status = Column(String, default="COMPLETED") # COMPLETED, FAILED, VOID
    cashier_id = Column(UUID(as_uuid=True))
    transaction_date = Column(DateTime(timezone=True), server_default=func.now())

class PharmacyRefundRecord(Base):
    __tablename__ = "pharmacy_refund_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_billing_records.id"), index=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("pharmacy_payment_transactions.id"), nullable=True)
    
    refund_amount = Column(Float)
    refund_mode = Column(String) # CASH, BANK_TRANSFER, CREDIT_NOTE
    refund_reason = Column(Text)
    
    authorized_by = Column(UUID(as_uuid=True))
    status = Column(String, default="APPROVED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PharmacyFinancialReport(Base):
    __tablename__ = "pharmacy_financial_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    report_type = Column(String, index=True) # DAILY_SALES, REVENUE_BY_MODE, COMPLIANCE_NARCOTICS
    report_date = Column(DateTime(timezone=True))
    generated_by = Column(UUID(as_uuid=True))
    
    data_payload = Column(JSON) # Storing the cached aggregated result arrays
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PharmacyBillingAuditLog(Base):
    __tablename__ = "pharmacy_billing_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    bill_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    patient_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    
    action = Column(String) # BILL_GENERATED, PAYMENT_RECEIVED, DISCOUNT_AUTHORIZED, REFUND_ISSUED
    action_details = Column(Text)
    
    performed_by = Column(UUID(as_uuid=True))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
