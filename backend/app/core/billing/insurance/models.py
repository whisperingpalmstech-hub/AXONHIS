import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class InsuranceProvider(Base):
    __tablename__ = "insurance_providers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_name = Column(String(200), nullable=False, unique=True)
    contact_details = Column(String(500), nullable=True)
    policy_rules = Column(String(1000), nullable=True)

class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("insurance_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_number = Column(String(100), nullable=False, unique=True)
    coverage_percentage = Column(Numeric(5, 2), nullable=False, default=100)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)

class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("insurance_providers.id", ondelete="RESTRICT"), nullable=False)
    claim_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), nullable=False, default="submitted")  # submitted, under_review, approved, rejected
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
