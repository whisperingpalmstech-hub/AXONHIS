from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import BillingEntry, FinancialAuditLog
from .schemas import BillingEntryCreate

class BillingEntryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_entry(self, data: BillingEntryCreate, user_id=None) -> BillingEntry:
        total = float(data.quantity) * float(data.unit_price)
        entry = BillingEntry(**data.model_dump(), total_price=total, status="pending")
        self.db.add(entry)
        await self.db.flush()
        
        audit = FinancialAuditLog(
            action="billing_entry_created",
            user_id=user_id,
            entity_type="billing_entry",
            entity_id=entry.id,
            details=f"Created billing entry for amount {total}"
        )
        self.db.add(audit)
        await self.db.flush()
        return entry

    async def create_entry_from_order(self, order) -> list[BillingEntry]:
        """Create billing entries from an approved order's items."""
        entries = []
        for item in order.items:
            entry = BillingEntry(
                encounter_id=order.encounter_id,
                order_id=order.id,
                patient_id=order.patient_id,
                service_id=item.id, # We assume item.id maps to service_id or we keep it simple for now
                quantity=float(item.quantity),
                unit_price=float(item.unit_price),
                total_price=float(item.unit_price) * float(item.quantity),
                status="pending"
            )
            self.db.add(entry)
            entries.append(entry)
        await self.db.flush()
        return entries

    async def reverse_entry_from_order(self, order) -> list[BillingEntry]:
        """Reverse all billing entries for a cancelled order."""
        result = await self.db.execute(
            select(BillingEntry).where(
                BillingEntry.order_id == order.id,
                BillingEntry.status == "pending",
            )
        )
        original_entries = list(result.scalars().all())
        reversal_entries = []
        for entry in original_entries:
            entry.status = "reversed"
            # In our new model, BillingReversal exists instead of self-referencing reversal_of
            from app.core.billing.billing_entries.models import BillingReversal
            reversal = BillingReversal(
                billing_entry_id=entry.id,
                reason="Order Cancelled",
                reversed_by=None
            )
            self.db.add(reversal)
            reversal_entries.append(reversal)
        await self.db.flush()
        return reversal_entries

    async def get_entries_for_encounter(self, encounter_id) -> list[BillingEntry]:
        result = await self.db.execute(
            select(BillingEntry)
            .where(BillingEntry.encounter_id == encounter_id)
            .order_by(BillingEntry.created_at)
        )
        return list(result.scalars().all())
