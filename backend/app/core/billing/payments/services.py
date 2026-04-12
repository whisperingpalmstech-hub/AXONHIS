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
        
        return pay
