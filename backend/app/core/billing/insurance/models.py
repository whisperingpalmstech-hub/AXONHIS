import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class InsuranceProvider(Base):
    __tablename__ = "insurance_providers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_name = Column(String(200), nullable=False, unique=True)
    provider_code = Column(String(50), unique=True, nullable=True)
    contact_details = Column(String(500), nullable=True)
    billing_address = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    
    packages = relationship("InsurancePackage", back_populates="provider")

class InsurancePackage(Base):
    __tablename__ = "insurance_packages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("insurance_providers.id", ondelete="CASCADE"), nullable=False)
    package_name = Column(String(200), nullable=False)
    
    # Generic rules
    default_co_pay_percent = Column(Numeric(5, 2), default=0) # Patient's share (e.g. 10%)
    default_deductible = Column(Numeric(12, 2), default=0) # Initial amount patient pays
    annual_limit = Column(Numeric(12, 2), nullable=True)
    
    # Category based overrides (JSON for simplicity: {"Surgery": 80, "Consultation": 100})
    coverage_details = Column(JSON, nullable=True) 
    
    provider = relationship("InsuranceProvider", back_populates="packages")
    policies = relationship("InsurancePolicy", back_populates="package")

class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    package_id = Column(UUID(as_uuid=True), ForeignKey("insurance_packages.id", ondelete="CASCADE"), nullable=False)
    policy_number = Column(String(100), nullable=False, unique=True)
    
    priority = Column(Numeric(2, 0), default=1) # 1=Primary, 2=Secondary
    group_number = Column(String(100), nullable=True)
    status = Column(String(20), default="active") # active, inactive, expired
    
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    
    package = relationship("InsurancePackage", back_populates="policies")
    # provider_id is removed as it's accessible via package.provider_id

class PreAuthorization(Base):
    __tablename__ = "pre_authorizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("insurance_providers.id"), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("billing_services.id"), nullable=False)
    
    auth_code = Column(String(100), nullable=True) 
    request_amount = Column(Numeric(12, 2), nullable=False)
    approved_amount = Column(Numeric(12, 2), default=0)
    
    status = Column(String(20), default="pending") # pending, approved, denied
    request_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    validity_date = Column(DateTime(timezone=True), nullable=True)
    clinical_notes = Column(String, nullable=True) 

class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("insurance_providers.id", ondelete="CASCADE"), nullable=False)
    
    claim_number = Column(String(100), unique=True, index=True)
    claim_amount = Column(Numeric(12, 2), nullable=False)
    allowed_amount = Column(Numeric(12, 2), default=0) 
    paid_amount = Column(Numeric(12, 2), default=0) 
    rejection_reason = Column(String(500), nullable=True)
    
    status = Column(String(50), nullable=False, default="submitted") 
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_updated = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    items = relationship("ClaimItem", back_populates="claim")

class ClaimItem(Base):
    __tablename__ = "claim_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("insurance_claims.id", ondelete="CASCADE"), nullable=False)
    billing_entry_id = Column(UUID(as_uuid=True), ForeignKey("billing_entries.id"), nullable=False)
    
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), default="pended") # approved, rejected, pended
    remark = Column(String(255), nullable=True)
    
    claim = relationship("InsuranceClaim", back_populates="items")
