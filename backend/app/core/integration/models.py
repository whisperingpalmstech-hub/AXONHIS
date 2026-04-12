"""
Cross-Module Integration Bridge
=================================
Central service that wires ER → Billing → IPD → Orders → Pharmacy together.
This is the "glue" that ensures no module works in isolation.

Business Flows:
1. ER-to-IPD Transfer: ER encounter → IPD admission → auto bed assign → billing deposit
2. Order-to-Bill: Clinical order → pricing engine → charge posting → RCM invoice
3. Discharge: Final bill → deposit settlement → discharge summary → pharmacy reconciliation
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import select, Column, String, Text, DateTime, Boolean, Numeric, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Base


class CrossModuleEvent(Base):
    """Audit trail for cross-module actions (ER→IPD, Order→Bill, etc.)"""
    __tablename__ = "cross_module_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # er_to_ipd, order_to_bill, discharge_settle, etc.
    source_module = Column(String(50), nullable=False)  # er, ipd, opd, orders, pharmacy, billing
    target_module = Column(String(50), nullable=False)
    source_id = Column(UUID(as_uuid=True), nullable=False)  # Source record ID
    target_id = Column(UUID(as_uuid=True), nullable=True)  # Target record ID (if created)
    patient_id = Column(UUID(as_uuid=True), nullable=True)
    payload = Column(JSONB, nullable=True)  # Additional context
    status = Column(String(30), default="completed")  # completed, failed, pending
    error_message = Column(Text, nullable=True)
    triggered_by = Column(UUID(as_uuid=True), nullable=False)
    triggered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ChargePosting(Base):
    """Centralized charge posting — every clinical action generates a charge here."""
    __tablename__ = "charge_postings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    encounter_type = Column(String(20), nullable=False)  # er, opd, ipd
    encounter_id = Column(UUID(as_uuid=True), nullable=False)  # ER/OPD/IPD encounter ID
    
    # Service details
    service_id = Column(UUID(as_uuid=True), nullable=True)  # billing_services.id
    service_code = Column(String(50), nullable=True)
    service_name = Column(String(255), nullable=False)
    service_group = Column(String(100), nullable=True)
    
    # Source
    source_module = Column(String(50), nullable=False)  # pharmacy, lab, radiology, procedure, consultation, bed, nursing
    source_order_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Pricing (from PricingEngine)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    net_amount = Column(Numeric(12, 2), nullable=False)
    is_stat = Column(Boolean, default=False)
    stat_surcharge = Column(Numeric(12, 2), default=0)
    tariff_plan_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Billing status
    is_billed = Column(Boolean, default=False)
    bill_id = Column(UUID(as_uuid=True), nullable=True)  # RCM bill it was added to
    is_cancelled = Column(Boolean, default=False)
    cancelled_reason = Column(Text, nullable=True)
    
    posted_by = Column(UUID(as_uuid=True), nullable=False)
    posted_by_name = Column(String(255), nullable=True)
    posted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PatientLedger(Base):
    """Real-time financial summary per patient visit."""
    __tablename__ = "patient_ledgers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    encounter_type = Column(String(20), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), nullable=False)
    
    total_charges = Column(Numeric(14, 2), default=0)
    total_discounts = Column(Numeric(14, 2), default=0)
    total_tax = Column(Numeric(14, 2), default=0)
    total_deposits = Column(Numeric(14, 2), default=0)
    total_payments = Column(Numeric(14, 2), default=0)
    total_insurance_covered = Column(Numeric(14, 2), default=0)
    outstanding_balance = Column(Numeric(14, 2), default=0)
    
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
