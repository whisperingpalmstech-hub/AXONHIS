from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
from datetime import datetime

from app.database import get_db
from app.dependencies import get_current_user
from app.core.auth.models import User

from .schemas import (
    ChartOfAccountsCreate,
    ChartOfAccountsOut,
    JournalEntryCreate,
    JournalEntryOut,
    JournalEntryPostRequest,
    ExportResponse
)
from .services import AccountingService

router = APIRouter(prefix="/accounting", tags=["Accounting"])

# ── Chart of Accounts ───────────────────────────────────────

@router.post("/accounts", response_model=ChartOfAccountsOut)
async def create_account(
    data: ChartOfAccountsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new account in the Chart of Accounts."""
    service = AccountingService(db)
    # Check if account code already exists
    accounts = await service.get_accounts()
    if any(a.account_code == data.account_code for a in accounts):
        raise HTTPException(status_code=400, detail="Account code already exists.")
    return await service.create_account(data)

@router.get("/accounts", response_model=List[ChartOfAccountsOut])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the full chart of accounts."""
    service = AccountingService(db)
    return await service.get_accounts()

@router.put("/accounts/{account_id}", response_model=ChartOfAccountsOut)
async def update_account(
    account_id: uuid.UUID,
    data: ChartOfAccountsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing account's details."""
    service = AccountingService(db)
    return await service.update_account(account_id, data)

@router.post("/accounts/{account_id}/status")
async def update_account_status(
    account_id: uuid.UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle account active/inactive status."""
    service = AccountingService(db)
    return await service.update_account_status(account_id, data.get('status', 'ACTIVE'))

# ── Journal Entries ─────────────────────────────────────────

@router.post("/journals", response_model=JournalEntryOut)
async def create_journal_entry(
    data: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new manual journal entry.
    Ensures that total debits equal total credits.
    """
    service = AccountingService(db)
    try:
        user_id = current_user.id
        return await service.create_journal_entry(data, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/journals", response_model=List[JournalEntryOut])
async def list_journal_entries(
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, POSTED, VOIDED)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all journal entries, optionally filtered by status."""
    service = AccountingService(db)
    return await service.get_journal_entries(status=status)

@router.post("/journals/{entry_id}/post", response_model=JournalEntryOut)
async def post_journal_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Post a draft journal entry.
    This locks the entry and updates the relevant account balances in the Chart of Accounts.
    """
    service = AccountingService(db)
    try:
        user_id = current_user.id
        return await service.post_journal_entry(entry_id, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Exports & Integrations ──────────────────────────────────

@router.get("/export/tally", response_model=ExportResponse)
async def export_to_tally(
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export all POSTED journal entries within the date range as Tally ERP9 compliant XML.
    """
    service = AccountingService(db)
    xml_data = await service.generate_tally_xml(start_date, end_date)
    return ExportResponse(
        format="xml",
        data=xml_data,
        filename=f"tally_export_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xml"
    )

# ── Financial Reporting ──────────────────────────────────────

@router.get("/reports/trial-balance")
async def get_trial_balance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Provides current balances for all accounts."""
    service = AccountingService(db)
    return await service.get_trial_balance()

@router.get("/reports/profit-and-loss")
async def get_profit_and_loss(
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculates revenue and expenses for a specific period."""
    service = AccountingService(db)
    return await service.get_profit_and_loss(start_date, end_date)

@router.get("/reports/balance-sheet")
async def get_balance_sheet(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Provides Assets, Liabilities and Equity balances."""
    service = AccountingService(db)
    return await service.get_balance_sheet()
