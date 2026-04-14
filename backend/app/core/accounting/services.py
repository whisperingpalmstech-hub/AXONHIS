import uuid
from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from .models import ChartOfAccounts, JournalEntry, JournalEntryLine, AccountStatus, JournalEntryStatus
from .schemas import ChartOfAccountsCreate, JournalEntryCreate

class AccountingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Chart of Accounts ───────────────────────────────────────

    async def create_account(self, data: ChartOfAccountsCreate) -> ChartOfAccounts:
        account = ChartOfAccounts(**data.model_dump())
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def get_accounts(self) -> List[ChartOfAccounts]:
        result = await self.db.execute(select(ChartOfAccounts).order_by(ChartOfAccounts.account_code))
        return list(result.scalars().all())

    async def update_account(self, account_id: uuid.UUID, data: ChartOfAccountsCreate) -> ChartOfAccounts:
        result = await self.db.execute(select(ChartOfAccounts).where(ChartOfAccounts.id == account_id))
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")
        
        for field, value in data.model_dump().items():
            setattr(account, field, value)
            
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def update_account_status(self, account_id: uuid.UUID, status: str) -> ChartOfAccounts:
        result = await self.db.execute(select(ChartOfAccounts).where(ChartOfAccounts.id == account_id))
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")
        account.status = status
        await self.db.commit()
        await self.db.refresh(account)
        return account

    # ── Journal Entries ─────────────────────────────────────────

    def _generate_entry_number(self, date: datetime) -> str:
        # Simplistic generation: JRN-<YYYYMMDD>-<UUID4>
        return f"JRN-{date.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    async def create_journal_entry(self, data: JournalEntryCreate, user_id: Optional[uuid.UUID] = None) -> JournalEntry:
        # Validate debits == credits
        total_debit = sum(line.debit_amount for line in data.lines)
        total_credit = sum(line.credit_amount for line in data.lines)
        
        if total_debit != total_credit:
            raise ValueError(f"Debits ({total_debit}) and Credits ({total_credit}) must be equal.")
            
        if total_debit <= 0:
            raise ValueError("Entry must have a positive non-zero value.")

        entry_date = data.entry_date or datetime.now(timezone.utc)
        entry_number = self._generate_entry_number(entry_date)

        # Create Entry Header
        entry = JournalEntry(
            entry_number=entry_number,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            entry_date=entry_date,
            description=data.description,
            status=JournalEntryStatus.DRAFT.value,
            total_debit=total_debit,
            total_credit=total_credit,
            integration_metadata=data.integration_metadata,
            created_by=user_id
        )
        self.db.add(entry)
        await self.db.flush() # get entry.id

        # Create Lines
        for line_data in data.lines:
            line = JournalEntryLine(
                journal_entry_id=entry.id,
                account_id=line_data.account_id,
                description=line_data.description,
                debit_amount=line_data.debit_amount,
                credit_amount=line_data.credit_amount,
                cost_center=line_data.cost_center
            )
            self.db.add(line)
        
        await self.db.commit()
        
        # Re-fetch with lines for serialization safety
        result_new = await self.db.execute(
            select(JournalEntry)
            .where(JournalEntry.id == entry.id)
            .options(selectinload(JournalEntry.lines))
        )
        return result_new.scalars().first()

    async def post_journal_entry(self, entry_id: uuid.UUID, user_id: uuid.UUID) -> JournalEntry:
        """
        Posts a journal entry: updates account balances and marks entry as POSTED.
        """
        result = await self.db.execute(select(JournalEntry).filter_by(id=entry_id))
        entry = result.scalars().first()
        
        if not entry:
            raise ValueError("Journal entry not found.")
            
        if entry.status != JournalEntryStatus.DRAFT.value:
            raise ValueError(f"Only DRAFT entries can be posted. Current status: {entry.status}")

        # Need to load the lines
        result_lines = await self.db.execute(select(JournalEntryLine).filter_by(journal_entry_id=entry_id))
        lines = result_lines.scalars().all()

        # Update account balances
        for line in lines:
            acc_result = await self.db.execute(select(ChartOfAccounts).filter_by(id=line.account_id))
            account = acc_result.scalars().first()
            if not account:
                raise ValueError(f"Account {line.account_id} not found.")

            # Standard double-entry accounting logic
            # Asset & Expense: Debit increases, Credit decreases
            # Liability, Equity & Revenue: Credit increases, Debit decreases
            if account.account_type in ["ASSET", "EXPENSE"]:
                # Normal balance is debit
                account.current_balance += (line.debit_amount - line.credit_amount)
            else:
                # Normal balance is credit
                account.current_balance += (line.credit_amount - line.debit_amount)

        # Mark entry as posted
        entry.status = JournalEntryStatus.POSTED.value
        entry.posted_at = datetime.now(timezone.utc)
        entry.posted_by = user_id

        await self.db.commit()
        
        # Re-fetch with lines
        result_final = await self.db.execute(
            select(JournalEntry)
            .where(JournalEntry.id == entry.id)
            .options(selectinload(JournalEntry.lines))
        )
        return result_final.scalars().first()

    async def get_journal_entries(self, status: Optional[str] = None) -> List[JournalEntry]:
        query = select(JournalEntry).options(selectinload(JournalEntry.lines)).order_by(JournalEntry.entry_date.desc())
        if status:
            query = query.filter_by(status=status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_trial_balance(self) -> List[dict]:
        """Provides current balances for all accounts."""
        accounts = await self.get_accounts()
        return [
            {
                "account_name": acc.account_name,
                "account_code": acc.account_code,
                "account_type": acc.account_type,
                "balance": float(acc.current_balance)
            }
            for acc in accounts
        ]

    async def get_profit_and_loss(self, start_date: datetime, end_date: datetime) -> dict:
        """Calculates revenue and expenses for a specific period."""
        from sqlalchemy import func
        
        query = select(
            ChartOfAccounts.account_name,
            ChartOfAccounts.account_type,
            func.sum(JournalEntryLine.debit_amount).label('total_debit'),
            func.sum(JournalEntryLine.credit_amount).label('total_credit')
        ).select_from(JournalEntryLine).join(JournalEntry).join(ChartOfAccounts).where(
            JournalEntry.status == JournalEntryStatus.POSTED.value,
            JournalEntry.entry_date >= start_date,
            JournalEntry.entry_date <= end_date,
            ChartOfAccounts.account_type.in_(["REVENUE", "EXPENSE"])
        ).group_by(ChartOfAccounts.account_name, ChartOfAccounts.account_type)

        result = await self.db.execute(query)
        rows = result.all()
        
        report = {"revenue": [], "expense": [], "total_revenue": 0.0, "total_expense": 0.0, "net_profit": 0.0}
        
        for name, acc_type, debit, credit in rows:
            debit = float(debit or 0)
            credit = float(credit or 0)
            
            if acc_type == "REVENUE":
                balance = credit - debit
                report["revenue"].append({"name": name, "amount": balance})
                report["total_revenue"] += balance
            else:
                balance = debit - credit
                report["expense"].append({"name": name, "amount": balance})
                report["total_expense"] += balance
        
        report["net_profit"] = report["total_revenue"] - report["total_expense"]
        return report

    async def get_balance_sheet(self) -> dict:
        """Provides Assets, Liabilities and Equity balances."""
        accounts = await self.get_accounts()
        report = {"assets": [], "liabilities": [], "equity": [], "total_assets": 0.0, "total_liabilities": 0.0, "total_equity": 0.0}
        
        for acc in accounts:
            balance = float(acc.current_balance)
            if acc.account_type == "ASSET":
                report["assets"].append({"name": acc.account_name, "amount": balance})
                report["total_assets"] += balance
            elif acc.account_type == "LIABILITY":
                report["liabilities"].append({"name": acc.account_name, "amount": balance})
                report["total_liabilities"] += balance
            elif acc.account_type == "EQUITY":
                report["equity"].append({"name": acc.account_name, "amount": balance})
                report["total_equity"] += balance
                
        return report

    # ── Export / Integrations ───────────────────────────────────

    async def generate_tally_xml(self, start_date: datetime, end_date: datetime) -> str:
        """Generates Tally ERP9 compliant XML for journal entries."""
        query = select(JournalEntry).filter(
            JournalEntry.entry_date >= start_date,
            JournalEntry.entry_date <= end_date,
            JournalEntry.status == JournalEntryStatus.POSTED.value
        ).order_by(JournalEntry.entry_date)
        
        result = await self.db.execute(query)
        entries = list(result.scalars().all())
        
        # Very basic Tally XML envelope builder
        xml = "<ENVELOPE>\n  <HEADER>\n    <TALLYREQUEST>Import Data</TALLYREQUEST>\n  </HEADER>\n  <BODY>\n    <IMPORTDATA>\n      <REQUESTDESC>\n        <REPORTNAME>Vouchers</REPORTNAME>\n        <STATICVARIABLES>\n          <SVCURRENTCOMPANY>AxonHIS</SVCURRENTCOMPANY>\n        </STATICVARIABLES>\n      </REQUESTDESC>\n      <REQUESTDATA>\n"
        
        for entry in entries:
            # Need lines for the entry
            line_result = await self.db.execute(select(JournalEntryLine).filter_by(journal_entry_id=entry.id))
            lines = line_result.scalars().all()
            
            entry_date_str = entry.entry_date.strftime("%Y%m%d")
            xml += f"        <TALLYMESSAGE xmlns:UDF=\"TallyUDF\">\n"
            xml += f"          <VOUCHER VCHTYPE=\"Journal\" ACTION=\"Create\" OBJVIEW=\"Accounting Voucher View\">\n"
            xml += f"            <DATE>{entry_date_str}</DATE>\n"
            xml += f"            <VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>\n"
            xml += f"            <VOUCHERNUMBER>{entry.entry_number}</VOUCHERNUMBER>\n"
            xml += f"            <NARRATION>{entry.description}</NARRATION>\n"
            
            for line in lines:
                acc_result = await self.db.execute(select(ChartOfAccounts).filter_by(id=line.account_id))
                account = acc_result.scalars().first()
                if not account: continue
                
                is_debit = line.debit_amount > 0
                amount = line.debit_amount if is_debit else line.credit_amount
                # Tally amounts: debit is negative in this specific XML structure usually, but depends on exact version. Let's use standard positive with ISDEBIT flag
                amount_str = f"-{amount}" if is_debit else f"{amount}"
                
                xml += f"            <ALLLEDGERENTRIES.LIST>\n"
                xml += f"              <LEDGERNAME>{account.account_name}</LEDGERNAME>\n"
                xml += f"              <ISDEBIT>{'Yes' if is_debit else 'No'}</ISDEBIT>\n"
                xml += f"              <AMOUNT>{amount_str}</AMOUNT>\n"
                xml += f"            </ALLLEDGERENTRIES.LIST>\n"
                
            xml += f"          </VOUCHER>\n"
            xml += f"        </TALLYMESSAGE>\n"

        xml += "      </REQUESTDATA>\n    </IMPORTDATA>\n  </BODY>\n</ENVELOPE>"
        return xml
