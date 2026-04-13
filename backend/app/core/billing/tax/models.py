"""Taxation Module Models for Billing."""
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Integer, Numeric, UUID
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid

from app.database import Base


class Tax(Base):
    """Tax master."""
    __tablename__ = "billing_taxes_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tax_code = Column(String(50), unique=True, nullable=False, index=True)
    tax_name = Column(String(200), nullable=False)
    tax_type = Column(String(50), nullable=False)  # 'gst', 'service_tax', 'vat', 'cess', 'surcharge'
    tax_percentage = Column(Numeric(5, 2), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class TaxApplicability(Base):
    """Tax applicability for services."""
    __tablename__ = "billing_tax_applicability_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tax_id = Column(UUID(as_uuid=True), ForeignKey("billing_taxes_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    service_name = Column(String(200), nullable=False)
    service_type = Column(String(50), nullable=False)  # 'hospital_service', 'lab', 'radiology', 'pharmacy'
    patient_category = Column(String(50), nullable=True)  # 'national', 'foreign', 'bpl'
    is_applicable = Column(Boolean, default=True)
    validity_start_date = Column(DateTime(timezone=True), nullable=True)
    validity_end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class TaxValidity(Base):
    """Tax validity periods."""
    __tablename__ = "billing_tax_validity_v2"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tax_id = Column(UUID(as_uuid=True), ForeignKey("billing_taxes_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    tax_percentage = Column(Numeric(5, 2), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
