import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, String, DateTime, Numeric, Boolean, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref

from app.database import Base


class AccountType(str, Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class JournalEntryStatus(str, Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    VOIDED = "VOIDED"


class ChartOfAccounts(Base):
    __tablename__ = "accounting_chart_of_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_code = Column(String(50), unique=True, nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)  # AccountType
    parent_account_id = Column(UUID(as_uuid=True), ForeignKey("accounting_chart_of_accounts.id"), nullable=True)
    description = Column(Text, nullable=True)
    is_control_account = Column(Boolean, default=False)
    status = Column(String(50), default=AccountStatus.ACTIVE.value)
    
    # Financial fields
    current_balance = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    children = relationship("ChartOfAccounts", backref=backref("parent", remote_side=[id]))


class JournalEntry(Base):
    __tablename__ = "accounting_journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_number = Column(String(100), unique=True, nullable=False, index=True)
    reference_type = Column(String(100), nullable=True)  # e.g., INVOICE, PAYMENT, RECEIPT
    reference_id = Column(UUID(as_uuid=True), nullable=True) # ID of the related invoice, etc.
    entry_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    description = Column(Text, nullable=False)
    status = Column(String(50), default=JournalEntryStatus.DRAFT.value)
    
    # Totals to ensure debits == credits
    total_debit = Column(Numeric(15, 2), default=Decimal('0.00'))
    total_credit = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Metadata for integrations (e.g. Tally voucher type)
    integration_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by = Column(UUID(as_uuid=True), nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    posted_by = Column(UUID(as_uuid=True), nullable=True)

    lines = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")


class JournalEntryLine(Base):
    __tablename__ = "accounting_journal_entry_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("accounting_journal_entries.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounting_chart_of_accounts.id"), nullable=False)
    
    description = Column(Text, nullable=True)
    debit_amount = Column(Numeric(15, 2), default=Decimal('0.00'))
    credit_amount = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Cost Center tracking (optional)
    cost_center = Column(String(100), nullable=True)
    
    journal_entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("ChartOfAccounts")
