import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from .models import Invoice
from app.core.billing.billing_entries.models import BillingEntry, FinancialAuditLog

class InvoiceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_invoice(self, patient_id: uuid.UUID, encounter_id: uuid.UUID, user_id=None) -> Invoice:
        # Find pending billing entries for this encounter
        res = await self.db.execute(
            select(BillingEntry).where(
                BillingEntry.encounter_id == encounter_id,
                BillingEntry.patient_id == patient_id,
                BillingEntry.status == "pending"
            )
        )
        entries = res.scalars().all()
        
        total = sum(float(e.total_price) for e in entries)
        
        # Integrate IPD Master Billing dynamically for IPD encounters
        try:
            from app.core.encounters.models import Encounter
            from app.core.ipd.models import IpdBillingMaster
            enc = (await self.db.execute(select(Encounter).where(Encounter.id == encounter_id))).scalar_one_or_none()
            if enc and enc.encounter_type == "IPD" and enc.encounter_uuid:
                ipd_res = await self.db.execute(
                    select(IpdBillingMaster).where(IpdBillingMaster.admission_number == enc.encounter_uuid)
                )
                ipd_master = ipd_res.scalar_one_or_none()
                if ipd_master and ipd_master.status != "Settled":
                    if ipd_master.outstanding_balance > 0:
                        total += float(ipd_master.outstanding_balance)
                    ipd_master.status = "Settled"
        except ImportError:
            pass
        
        inv = Invoice(
            patient_id=patient_id,
            encounter_id=encounter_id,
            invoice_number=f"INV-{str(uuid.uuid4())[:8].upper()}",
            total_amount=total,
            status="issued"
        )
        self.db.add(inv)
        await self.db.flush()
        
        for e in entries:
            e.status = "charged"
            
        audit = FinancialAuditLog(
            action="invoice_generated",
            user_id=user_id,
            entity_type="invoice",
            entity_id=inv.id,
            details=f"Generated invoice {inv.invoice_number} for amount {total}"
        )
        self.db.add(audit)
        await self.db.flush()

        # ── AUTO-JOURNAL INTEGRATION (Accrual) ─────────────────
        try:
            from app.core.accounting.services import AccountingService
            from app.core.accounting.schemas import JournalEntryCreate, JournalEntryLineCreate
            from app.core.accounting.models import ChartOfAccounts
            
            accounting_service = AccountingService(self.db)
            
            # Debit: Patient Receivables (1005)
            rec_res = await self.db.execute(select(ChartOfAccounts).where(ChartOfAccounts.account_code == "1005"))
            receivable_acc = rec_res.scalars().first()
            
            # Credit: Service Revenue (4001)
            rev_res = await self.db.execute(select(ChartOfAccounts).where(ChartOfAccounts.account_code == "4001"))
            revenue_acc = rev_res.scalars().first()
            
            if receivable_acc and revenue_acc:
                journal_data = JournalEntryCreate(
                    description=f"Accrual: Invoice {inv.invoice_number} Generated",
                    entry_date=datetime.now(),
                    reference_type="invoice",
                    reference_id=inv.id,
                    lines=[
                        JournalEntryLineCreate(
                            account_id=receivable_acc.id,
                            debit_amount=inv.total_amount,
                            credit_amount=0,
                            description=f"Awaiting payment for invoice {inv.invoice_number}"
                        ),
                        JournalEntryLineCreate(
                            account_id=revenue_acc.id,
                            debit_amount=0,
                            credit_amount=inv.total_amount,
                            description=f"Revenue recognized for invoice {inv.invoice_number}"
                        )
                    ]
                )
                
                # Create and Auto-Post
                entry = await accounting_service.create_journal_entry(journal_data, user_id=user_id)
                await accounting_service.post_journal_entry(entry.id, user_id=user_id if user_id else uuid.uuid4())
                
        except Exception as e:
            print(f"FAILED TO CREATE AUTO-JOURNAL FOR INVOICE: {e}")
        
        return inv
