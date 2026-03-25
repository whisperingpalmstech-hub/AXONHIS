import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from typing import List, Optional

from .models import (
    PharmacyIPPendingIssue, PharmacyIPDispenseRecord,
    PharmacyIPDispenseBatch, PharmacyIPOrderLog, PharmacyIPBillingRecord
)
from .schemas import IPPendingIssueCreate, IPDispenseSubmission


class IPIssuesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Audit Logging ─────────────────────────────────────────────────
    async def _log(self, issue_id: uuid.UUID, action: str,
                   pharmacist_id: uuid.UUID, details: dict = None):
        log = PharmacyIPOrderLog(
            issue_id=issue_id,
            pharmacist_id=pharmacist_id,
            action_type=action,
            details=details or {}
        )
        self.db.add(log)

    # ── Create IP Issue (From Doctor / Nursing) ───────────────────────
    async def create_issue(self, data: IPPendingIssueCreate) -> PharmacyIPPendingIssue:
        issue = PharmacyIPPendingIssue(
            patient_id=data.patient_id,
            patient_name=data.patient_name,
            uhid=data.uhid,
            admission_number=data.admission_number,
            ward=data.ward,
            bed_number=data.bed_number,
            treating_doctor_name=data.treating_doctor_name,
            source=data.source,
            priority=data.priority,
            status="Pending",
        )
        self.db.add(issue)
        await self.db.flush()

        for item_data in data.items:
            item = PharmacyIPDispenseRecord(
                issue_id=issue.id,
                drug_id=item_data.drug_id,
                medication_name=item_data.medication_name,
                dosage=item_data.dosage,
                frequency=item_data.frequency,
                route=item_data.route,
                prescribed_quantity=Decimal(str(item_data.prescribed_quantity)),
                is_non_formulary=item_data.is_non_formulary,
                store_id=item_data.store_id,
                store_name=item_data.store_name,
                status="Pending",
            )
            self.db.add(item)

        await self.db.commit()
        await self.db.refresh(issue)
        return issue

    # ── Get IP Issues ─────────────────────────────────────────────────
    async def list_issues(self, status: str = None) -> List[PharmacyIPPendingIssue]:
        q = select(PharmacyIPPendingIssue).options(
            selectinload(PharmacyIPPendingIssue.items).selectinload(PharmacyIPDispenseRecord.batches)
        )
        if status:
            q = q.where(PharmacyIPPendingIssue.status == status)
        q = q.order_by(
            case(
                {"STAT": 1, "Urgent": 2, "Routine": 3},
                value=PharmacyIPPendingIssue.priority,
                else_=99
            ),
            PharmacyIPPendingIssue.order_date.desc()
        )
        res = await self.db.execute(q)
        return list(res.scalars().all())

    async def get_issue(self, issue_id: uuid.UUID) -> PharmacyIPPendingIssue:
        q = select(PharmacyIPPendingIssue).options(
            selectinload(PharmacyIPPendingIssue.items).selectinload(PharmacyIPDispenseRecord.batches),
            selectinload(PharmacyIPPendingIssue.billing),
            selectinload(PharmacyIPPendingIssue.logs)
        ).where(PharmacyIPPendingIssue.id == issue_id)
        issue = (await self.db.execute(q)).scalar_one_or_none()
        if not issue:
            raise HTTPException(404, "Issue not found")
        return issue

    # ── Dispense & IPD Billing Integration ────────────────────────────
    async def process_dispense(self, issue_id: uuid.UUID,
                               submission: IPDispenseSubmission, pharmacist_id: uuid.UUID):
        issue = await self.get_issue(issue_id)
        if issue.status == "Completed":
            raise HTTPException(400, "Issue is already completed")

        from app.core.pharmacy.inventory.models import InventoryItem
        from app.core.pharmacy.batches.models import DrugBatch

        dispensed_count = 0
        total_items = len(issue.items)

        # Build mapping of submitted items
        sub_items = {s.record_id: s for s in submission.items}

        for item in issue.items:
            if item.status == "Dispensed":
                dispensed_count += 1
                continue

            sub_item = sub_items.get(item.id)
            if not sub_item:
                continue

            # Process Substitution if present
            item.substituted_for = sub_item.substituted_for
            if sub_item.substituted_for:
                 item.medication_name = sub_item.medication_name
                 item.drug_id = sub_item.drug_id

            item.dispensed_quantity = Decimal(str(sub_item.dispensed_quantity))
            item.instructions = sub_item.instructions
            item.status = "Dispensed"
            dispensed_count += 1

            charge_amount = Decimal("0.00")

            # Deduct inventory & bind batches
            if not item.is_non_formulary and item.drug_id:
                # Deduct total inventory
                q_inv = select(InventoryItem).where(InventoryItem.drug_id == item.drug_id)
                inv = (await self.db.execute(q_inv)).scalar_one_or_none()
                if not inv or float(inv.quantity_available) < float(item.dispensed_quantity):
                    raise HTTPException(400, f"Insufficient overall stock for {item.medication_name}")
                inv.quantity_available = float(inv.quantity_available) - float(item.dispensed_quantity)

                # Deduct batch level & compute exact price
                for b_sub in sub_item.batches:
                    qty_to_deduct = Decimal(str(b_sub.quantity_deducted))
                    q_batch = select(DrugBatch).where(DrugBatch.id == b_sub.batch_id)
                    batch = (await self.db.execute(q_batch)).scalar_one_or_none()

                    if not batch or batch.quantity < qty_to_deduct:
                        raise HTTPException(400, f"Insufficient stock in batch {b_sub.batch_number}")
                    batch.quantity -= qty_to_deduct

                    # Calculate charge amount from batch price
                    # If batch model has unit_price, use it, else default to 10
                    unit_price = Decimal(str(getattr(batch, 'unit_price', 10.00)))
                    charge_amount += (qty_to_deduct * unit_price)

                    # Record batch usage
                    item.batches.append(PharmacyIPDispenseBatch(
                        batch_id=batch.id,
                        batch_number=batch.batch_number,
                        quantity_deducted=qty_to_deduct,
                        expiry_date=batch.expiry_date
                    ))
            else:
                # Non-formulary items use manual unit price input
                charge_amount = Decimal(str(item.dispensed_quantity)) * Decimal(str(sub_item.unit_price))

            # Push to IPD Billing
            issue.billing.append(PharmacyIPBillingRecord(
                item_id=item.id,
                charge_amount=charge_amount,
                billing_synced=False  # Handled by a Celery worker in a real scenario
            ))

        # Update Master Status
        if dispensed_count == total_items:
            issue.status = "Completed"
        elif dispensed_count > 0:
            issue.status = "In Progress"

        # Log action
        await self._log(issue.id, "DISPENSED", pharmacist_id, details={
            "items_processed": len(submission.items),
            "new_status": issue.status
        })

        await self.db.commit()
        await self.db.refresh(issue)
        return issue

    # ── Audit Trail ───────────────────────────────────────────────────
    async def get_audit_trail(self, issue_id: uuid.UUID) -> List[PharmacyIPOrderLog]:
        q = select(PharmacyIPOrderLog).where(
            PharmacyIPOrderLog.issue_id == issue_id
        ).order_by(PharmacyIPOrderLog.timestamp.desc())
        res = await self.db.execute(q)
        return list(res.scalars().all())

    # ── Multi-store Inventory Lookup ──────────────────────────────────
    async def lookup_stock(self, drug_id: uuid.UUID) -> List[dict]:
        """Provides simulated multi-store availability logic."""
        # Simulated response for stores: Main Pharmacy, Ward Pharmacy, Emergency Pharmacy
        from app.core.pharmacy.inventory.models import InventoryItem
        q = select(InventoryItem).where(InventoryItem.drug_id == drug_id)
        inv = (await self.db.execute(q)).scalar_one_or_none()
        
        main_qty = float(inv.quantity_available) if inv else 0.0
        return [
            {"store_id": "00000000-0000-0000-0000-000000000001", "store_name": "Main Pharmacy", "quantity": main_qty},
            {"store_id": "00000000-0000-0000-0000-000000000002", "store_name": "Ward Pharmacy D", "quantity": 0.0},
            {"store_id": "00000000-0000-0000-0000-000000000003", "store_name": "Emergency Pharmacy", "quantity": 5.0},
        ]
