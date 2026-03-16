"""Billing services – deterministic billing from orders with full traceability."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.billing.models import BillingEntry, BillingEntryStatus
from app.core.orders.models import Order


class BillingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_entry_from_order(self, order: Order) -> list[BillingEntry]:
        """Create billing entries from an approved order's items. One entry per item."""
        entries = []
        for item in order.items:
            entry = BillingEntry(
                encounter_id=order.encounter_id,
                order_id=order.id,
                patient_id=order.patient_id,
                description=f"{order.order_type}: {item.item_name}",
                amount=float(item.unit_price) * float(item.quantity),
            )
            self.db.add(entry)
            entries.append(entry)
        await self.db.flush()
        return entries

    async def reverse_entry_from_order(self, order: Order) -> list[BillingEntry]:
        """Reverse all billing entries for a cancelled order."""
        result = await self.db.execute(
            select(BillingEntry).where(
                BillingEntry.order_id == order.id,
                BillingEntry.status == BillingEntryStatus.ACTIVE,
            )
        )
        original_entries = list(result.scalars().all())
        reversal_entries = []
        for entry in original_entries:
            entry.status = BillingEntryStatus.REVERSED
            reversal = BillingEntry(
                encounter_id=entry.encounter_id,
                order_id=order.id,
                patient_id=entry.patient_id,
                description=f"REVERSAL: {entry.description}",
                amount=-entry.amount,
                status=BillingEntryStatus.REVERSED,
                reversal_of=entry.id,
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
