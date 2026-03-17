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
        
        inv = Invoice(
            patient_id=patient_id,
            encounter_id=encounter_id,
            invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
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
        
        return inv
