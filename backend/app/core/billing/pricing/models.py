"""Variable Pricing Engine Models for Billing Module."""
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, Integer, Numeric, UUID
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid

from app.database import Base


class BaseRate(Base):
    """Base rate for services."""
    __tablename__ = "billing_base_rates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    service_name = Column(String(200), nullable=False)
    base_price = Column(Numeric(12, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class RateVariation(Base):
    """Rate variations by patient category, bed type, payment entitlement."""
    __tablename__ = "billing_rate_variations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    base_rate_id = Column(UUID(as_uuid=True), ForeignKey("billing_base_rates.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_category = Column(String(50), nullable=False)  # 'national', 'foreign', 'bpl', 'employee', 'nok_employee'
    bed_type = Column(String(50), nullable=True)  # 'general', 'private', 'semi_private', 'icu'
    payment_entitlement = Column(String(50), nullable=True)  # 'self', 'insurance', 'corporate', 'stat'
    variation_type = Column(String(50), nullable=False)  # 'percentage', 'fixed', 'multiplier'
    variation_value = Column(Numeric(12, 2), nullable=False)  # e.g., 10 for 10%, 100 for fixed amount, 1.5 for multiplier
    validity_start_date = Column(DateTime(timezone=True), nullable=True)
    validity_end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class RateValidity(Base):
    """Rate validity periods."""
    __tablename__ = "billing_rate_validity"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    base_rate_id = Column(UUID(as_uuid=True), ForeignKey("billing_base_rates.id", ondelete="CASCADE"), nullable=False, index=True)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class AfterHoursCharge(Base):
    """After-hours charging rules."""
    __tablename__ = "billing_after_hours_charges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    service_name = Column(String(200), nullable=False)
    start_time = Column(String(10), nullable=False)  # '18:00'
    end_time = Column(String(10), nullable=False)  # '08:00'
    days_applicable = Column(JSONB, nullable=False)  # ['monday', 'tuesday', ...]
    charge_type = Column(String(50), nullable=False)  # 'percentage', 'fixed', 'multiplier'
    charge_value = Column(Numeric(12, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Currency(Base):
    """Multi-currency support."""
    __tablename__ = "billing_currencies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    currency_code = Column(String(3), nullable=False, unique=True)  # 'USD', 'EUR', 'INR'
    currency_name = Column(String(50), nullable=False)
    currency_symbol = Column(String(5), nullable=False)  # '$', '€', '₹'
    is_base_currency = Column(Boolean, default=False)
    exchange_rate_to_base = Column(Numeric(12, 6), nullable=False)  # 1 foreign = x base
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ExchangeRate(Base):
    """Exchange rate tracking."""
    __tablename__ = "billing_exchange_rates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_currency_id = Column(UUID(as_uuid=True), ForeignKey("billing_currencies.id", ondelete="CASCADE"), nullable=False, index=True)
    to_currency_id = Column(UUID(as_uuid=True), ForeignKey("billing_currencies.id", ondelete="CASCADE"), nullable=False, index=True)
    rate = Column(Numeric(12, 6), nullable=False)
    effective_from = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    source = Column(String(50), nullable=True)  # 'manual', 'api', 'system'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
