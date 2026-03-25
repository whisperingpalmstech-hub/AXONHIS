import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from typing import List, Optional

from .models import (
    PharmacySalesReturn, PharmacyReturnItem, PharmacyReturnReason,
    PharmacyReturnRefund, PharmacyReturnLog
)
from .schemas import SalesReturnCreate, ProcessRefundRequest

# Controlled drug codes that cannot be returned
CONTROLLED_DRUG_CODES = {"MORPHINE", "FENTANYL", "OXYCODONE", "CODEINE", "TRAMADOL"}
RETURN_WINDOW_DAYS = 7  # Max days after sale for returns


class SalesReturnsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Return Number Generation ──────────────────────────────────────
    async def _generate_return_number(self) -> str:
        year = datetime.now(timezone.utc).year
        res = await self.db.execute(select(func.count(PharmacySalesReturn.id)))
        count = res.scalar() or 0
        return f"RET-{year}-{(count + 1):06d}"

    # ── Audit Logging ─────────────────────────────────────────────────
    async def _log(self, return_id: uuid.UUID, action: str,
                   pharmacist_id: uuid.UUID = None, details: dict = None):
        log = PharmacyReturnLog(
            return_id=return_id,
            pharmacist_id=pharmacist_id,
            action_type=action,
            details=details or {}
        )
        self.db.add(log)

    # ── Eligibility Validation ────────────────────────────────────────
    def _validate_item_eligibility(self, item_data, sale_date: datetime = None):
        """Validate whether a medication is eligible for return."""
        is_eligible = True
        notes = []

        # Rule 1: Return time window
        if sale_date:
            days_since = (datetime.now(timezone.utc) - sale_date).days
            if days_since > RETURN_WINDOW_DAYS:
                is_eligible = False
                notes.append(f"Return window expired ({days_since} days, max {RETURN_WINDOW_DAYS})")

        # Rule 2: Controlled substances
        med_name = item_data.medication_name.upper()
        for code in CONTROLLED_DRUG_CODES:
            if code in med_name:
                is_eligible = False
                notes.append(f"Controlled substance ({code}) - return not permitted")

        # Rule 3: Quantity check
        if item_data.quantity_returned > item_data.quantity_sold:
            is_eligible = False
            notes.append("Return quantity exceeds sold quantity")

        if item_data.quantity_returned <= 0:
            is_eligible = False
            notes.append("Return quantity must be greater than zero")

        return is_eligible, "; ".join(notes) if notes else "Eligible for return"

    # ── Create Return ─────────────────────────────────────────────────
    async def create_return(self, data: SalesReturnCreate) -> PharmacySalesReturn:
        return_number = await self._generate_return_number()

        total_refund = Decimal("0.00")
        return_items = []

        for item_data in data.items:
            is_eligible, note = self._validate_item_eligibility(item_data, data.sale_date)
            refund_amount = Decimal(str(item_data.quantity_returned)) * Decimal(str(item_data.unit_price))

            if is_eligible:
                total_refund += refund_amount

            return_items.append(PharmacyReturnItem(
                drug_id=item_data.drug_id,
                medication_name=item_data.medication_name,
                batch_id=item_data.batch_id,
                batch_number=item_data.batch_number,
                quantity_sold=item_data.quantity_sold,
                quantity_returned=item_data.quantity_returned,
                unit_price=item_data.unit_price,
                refund_amount=refund_amount if is_eligible else Decimal("0.00"),
                reason_text=item_data.reason_text,
                is_eligible=is_eligible,
                eligibility_note=note,
                stock_restored=False,
            ))

        sales_return = PharmacySalesReturn(
            return_number=return_number,
            sale_id=data.sale_id,
            bill_number=data.bill_number,
            patient_name=data.patient_name,
            uhid=data.uhid,
            mobile=data.mobile,
            total_refund_amount=total_refund,
            net_refund=total_refund,
            status="Pending",
            sale_date=data.sale_date,
            notes=data.notes,
            items=return_items,
        )
        self.db.add(sales_return)
        await self.db.flush()

        await self._log(sales_return.id, "RETURN_CREATED", details={
            "return_number": return_number,
            "items_count": len(data.items),
            "total_refund": str(total_refund),
        })

        await self.db.commit()
        await self.db.refresh(sales_return)
        return sales_return

    # ── Process Refund ────────────────────────────────────────────────
    async def process_refund(self, return_id: uuid.UUID,
                              data: ProcessRefundRequest) -> PharmacySalesReturn:
        q = select(PharmacySalesReturn).options(
            selectinload(PharmacySalesReturn.items)
        ).where(PharmacySalesReturn.id == return_id)
        ret = (await self.db.execute(q)).scalar_one_or_none()
        if not ret:
            raise HTTPException(404, "Return not found")
        if ret.status == "Completed":
            raise HTTPException(400, "Return already completed")

        # Create refund record
        refund = PharmacyReturnRefund(
            return_id=ret.id,
            refund_amount=ret.net_refund,
            refund_mode=data.refund_mode,
            transaction_ref=data.transaction_ref,
        )
        self.db.add(refund)

        # Stock reconciliation – restore eligible items
        for item in ret.items:
            if item.is_eligible and not item.stock_restored:
                if item.drug_id:
                    await self._restore_stock(item.drug_id, item.batch_id,
                                               item.quantity_returned)
                item.stock_restored = True

        ret.status = "Completed"

        await self._log(ret.id, "REFUND_PROCESSED", details={
            "refund_amount": str(ret.net_refund),
            "refund_mode": data.refund_mode,
            "items_restored": sum(1 for i in ret.items if i.stock_restored),
        })

        await self.db.commit()
        await self.db.refresh(ret)
        return ret

    # ── Stock Restoration ─────────────────────────────────────────────
    async def _restore_stock(self, drug_id: uuid.UUID,
                              batch_id: uuid.UUID, quantity: Decimal):
        from app.core.pharmacy.inventory.models import InventoryItem
        from app.core.pharmacy.batches.models import DrugBatch

        # Restore aggregate inventory
        q_inv = select(InventoryItem).where(InventoryItem.drug_id == drug_id)
        inv = (await self.db.execute(q_inv)).scalar_one_or_none()
        if inv:
            inv.quantity_available = float(inv.quantity_available) + float(quantity)

        # Restore batch quantity
        if batch_id:
            q_batch = select(DrugBatch).where(DrugBatch.id == batch_id)
            batch = (await self.db.execute(q_batch)).scalar_one_or_none()
            if batch:
                batch.quantity = float(batch.quantity) + float(quantity)

    # ── List Returns ──────────────────────────────────────────────────
    async def list_returns(self, status: str = None) -> List[PharmacySalesReturn]:
        q = select(PharmacySalesReturn).options(
            selectinload(PharmacySalesReturn.items),
            selectinload(PharmacySalesReturn.refund)
        )
        if status:
            q = q.where(PharmacySalesReturn.status == status)
        q = q.order_by(PharmacySalesReturn.created_at.desc())
        res = await self.db.execute(q)
        return list(res.scalars().all())

    # ── Get Single Return ─────────────────────────────────────────────
    async def get_return(self, return_id: uuid.UUID) -> PharmacySalesReturn:
        q = select(PharmacySalesReturn).options(
            selectinload(PharmacySalesReturn.items),
            selectinload(PharmacySalesReturn.refund)
        ).where(PharmacySalesReturn.id == return_id)
        ret = (await self.db.execute(q)).scalar_one_or_none()
        if not ret:
            raise HTTPException(404, "Return not found")
        return ret

    # ── Audit Logs ────────────────────────────────────────────────────
    async def get_audit_logs(self, return_id: uuid.UUID) -> List[PharmacyReturnLog]:
        q = select(PharmacyReturnLog).where(
            PharmacyReturnLog.return_id == return_id
        ).order_by(PharmacyReturnLog.timestamp.desc())
        res = await self.db.execute(q)
        return list(res.scalars().all())

    # ── Return Reasons ────────────────────────────────────────────────
    async def list_reasons(self) -> List[PharmacyReturnReason]:
        q = select(PharmacyReturnReason).where(PharmacyReturnReason.is_active == True)
        res = await self.db.execute(q)
        return list(res.scalars().all())

    async def seed_reasons(self):
        reasons = [
            ("UNUSED", "Unused medication", False),
            ("WRONG_MED", "Wrong medication dispensed", True),
            ("ADR", "Adverse drug reaction", True),
            ("PATIENT_REFUSAL", "Patient refusal", False),
            ("EXPIRED", "Medication expired before use", False),
            ("DOSAGE_CHANGE", "Dosage changed by doctor", False),
            ("DUPLICATE", "Duplicate dispensing", True),
        ]
        for code, text, approval in reasons:
            existing = await self.db.execute(
                select(PharmacyReturnReason).where(PharmacyReturnReason.reason_code == code)
            )
            if not existing.scalar_one_or_none():
                self.db.add(PharmacyReturnReason(
                    reason_code=code, reason_text=text,
                    requires_approval=approval
                ))
        await self.db.commit()

    # ── Bill Search (from walk-in sales) ──────────────────────────────
    async def search_bills(self, query: str) -> list:
        from app.core.pharmacy.sales.models import PharmacyWalkInSale, PharmacySaleItem
        q_lower = query.lower()

        q = select(PharmacyWalkInSale).options(
            selectinload(PharmacyWalkInSale.items)
        ).where(PharmacyWalkInSale.status == "completed")

        # Try to search by multiple fields
        from sqlalchemy import or_, cast, String
        q = q.where(or_(
            cast(PharmacyWalkInSale.id, String).ilike(f"%{q_lower}%"),
            PharmacyWalkInSale.walkin_name.ilike(f"%{q_lower}%"),
            PharmacyWalkInSale.walkin_mobile.ilike(f"%{q_lower}%"),
        )).order_by(PharmacyWalkInSale.sale_date.desc()).limit(20)

        res = await self.db.execute(q)
        sales = res.scalars().all()

        results = []
        for sale in sales:
            items_data = []
            for item in sale.items:
                from app.core.pharmacy.medications.models import Medication
                med_q = select(Medication).where(Medication.id == item.drug_id)
                med = (await self.db.execute(med_q)).scalar_one_or_none()
                items_data.append({
                    "drug_id": str(item.drug_id),
                    "medication_name": med.drug_name if med else "Unknown",
                    "batch_id": str(item.batch_id),
                    "quantity": float(item.quantity),
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.total_price),
                })

            results.append({
                "id": str(sale.id),
                "bill_number": str(sale.id)[:8].upper(),
                "patient_name": sale.walkin_name or "Walk-In",
                "uhid": "",
                "mobile": sale.walkin_mobile or "",
                "sale_date": sale.sale_date.isoformat(),
                "total_amount": float(sale.net_amount),
                "status": sale.status,
                "items": items_data,
            })
        return results
