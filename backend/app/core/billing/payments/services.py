import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Payment
from app.core.billing.invoices.models import Invoice
from app.core.billing.billing_entries.models import FinancialAuditLog

class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_payment(self, data, user_id=None) -> Payment:
        pay = Payment(**data.model_dump(), payment_status="completed")
        self.db.add(pay)
        await self.db.flush()
        
        inv = await self.db.get(Invoice, data.invoice_id)
        if inv:
            # Check if total paid = invoice amount
            paid_res = await self.db.execute(select(Payment).where(Payment.invoice_id == inv.id))
            total_paid = sum(float(p.amount) for p in paid_res.scalars().all())
            
            if total_paid >= float(inv.total_amount):
                inv.status = "paid"
            else:
                inv.status = "partially_paid"
                
        audit = FinancialAuditLog(
            action="payment_received",
            user_id=user_id,
            entity_type="payment",
            entity_id=pay.id,
            details=f"Received payment of {pay.amount} via {pay.payment_method}"
        )
        self.db.add(audit)
        await self.db.flush()

        # ── AUTO-JOURNAL INTEGRATION ────────────────────────────
        try:
            from app.core.accounting.services import AccountingService
            from app.core.accounting.schemas import JournalEntryCreate, JournalEntryLineCreate
            from app.core.accounting.models import ChartOfAccounts
            
            accounting_service = AccountingService(self.db)
            
            # 1. Determine accounts
            # In a real system, these would be in a Config/Master table
            # For now, we'll look them up by common codes/names
            
            # Debit Account (Cash or Bank)
            is_cash = pay.payment_method.lower() in ["cash", "counter"]
            target_code = "1001" if is_cash else "1002" # 1001 for Cash, 1002 for Bank
            
            acc_res = await self.db.execute(select(ChartOfAccounts).where(ChartOfAccounts.account_code == target_code))
            debit_acc = acc_res.scalars().first()
            
            # Credit Account (Usually Patient Receivable for invoice payments)
            # In Accrual accounting, the Invoice already recognized Revenue.
            # So Payment reduces the Receivable.
            rev_res = await self.db.execute(select(ChartOfAccounts).where(ChartOfAccounts.account_code == "1005"))
            credit_acc = rev_res.scalars().first()
            
            if debit_acc and credit_acc:
                journal_data = JournalEntryCreate(
                    description=f"Auto-Journal: Payment for Invoice {inv.invoice_number if inv else 'N/A'}",
                    entry_date=datetime.now(),
                    reference_type="payment",
                    reference_id=pay.id,
                    integration_metadata={"payment_method": pay.payment_method},
                    lines=[
                        JournalEntryLineCreate(
                            account_id=debit_acc.id,
                            debit_amount=pay.amount,
                            credit_amount=0,
                            description=f"Received via {pay.payment_method}"
                        ),
                        JournalEntryLineCreate(
                            account_id=credit_acc.id,
                            debit_amount=0,
                            credit_amount=pay.amount,
                            description=f"Revenue recognized for invoice {inv.id if inv else ''}"
                        )
                    ]
                )
                
                # Create and Auto-Post
                entry = await accounting_service.create_journal_entry(journal_data, user_id=user_id)
                await accounting_service.post_journal_entry(entry.id, user_id=user_id if user_id else uuid.uuid4())
                
        except Exception as e:
            # We don't want to fail the payment if accounting sync fails, but we should log it
            print(f"FAILED TO CREATE AUTO-JOURNAL: {e}")
        
        return pay
