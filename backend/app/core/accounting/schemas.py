from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal

# ── Chart of Accounts ───────────────────────────────────────

class ChartOfAccountsBase(BaseModel):
    account_code: str = Field(..., max_length=50)
    account_name: str = Field(..., max_length=255)
    account_type: str = Field(..., max_length=50)
    parent_account_id: Optional[UUID] = None
    description: Optional[str] = None
    is_control_account: bool = False
    status: str = "ACTIVE"

class ChartOfAccountsCreate(ChartOfAccountsBase):
    pass

class ChartOfAccountsOut(ChartOfAccountsBase):
    id: UUID
    current_balance: Decimal
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# ── Journal Entries ─────────────────────────────────────────

class JournalEntryLineCreate(BaseModel):
    account_id: UUID
    description: Optional[str] = None
    debit_amount: Decimal = Field(default=Decimal('0.00'))
    credit_amount: Decimal = Field(default=Decimal('0.00'))
    cost_center: Optional[str] = None

class JournalEntryCreate(BaseModel):
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    entry_date: Optional[datetime] = None
    description: str
    lines: List[JournalEntryLineCreate]
    integration_metadata: Optional[Dict[str, Any]] = None

class JournalEntryLineOut(BaseModel):
    id: UUID
    account_id: UUID
    description: Optional[str]
    debit_amount: Decimal
    credit_amount: Decimal
    cost_center: Optional[str]
    
    class Config:
        from_attributes = True

class JournalEntryOut(BaseModel):
    id: UUID
    entry_number: str
    reference_type: Optional[str]
    reference_id: Optional[UUID]
    entry_date: datetime
    description: str
    status: str
    total_debit: Decimal
    total_credit: Decimal
    created_at: datetime
    created_by: Optional[UUID]
    
    lines: List[JournalEntryLineOut] = []
    
    class Config:
        from_attributes = True

# ── Post Request ────────────────────────────────────────────

class JournalEntryPostRequest(BaseModel):
    user_id: UUID 

# ── Export ──────────────────────────────────────────────────

class ExportResponse(BaseModel):
    format: str
    data: str
    filename: str
