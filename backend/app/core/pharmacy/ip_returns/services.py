import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from typing import List

from .models import (
    PharmacyIPReturn, PharmacyIPReturnItem,
    PharmacyIPBillingAdjustment, PharmacyIPReturnLog
)
from .schemas import IPReturnCreate, IPReturnProcess
from ...pharmacy.ip_issues.models import PharmacyIPPendingIssue, PharmacyIPDispenseRecord

class IPReturnsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Audit Logging ─────────────────────────────────────────────────
    async def _log(self, return_id: uuid.UUID, action: str,
                   user_id: uuid.UUID | None, details: dict = None):
        log = PharmacyIPReturnLog(
            return_id=return_id,
            user_id=user_id,
            action_type=action,
            details=details or {}
        )
        self.db.add(log)

    # ── Create Return/Rejection (By Nursing) ──────────────────────────
    async def create_return_request(self, data: IPReturnCreate) -> PharmacyIPReturn:
        # Verify the original issue exists
        issue = await self.db.execute(
            select(PharmacyIPPendingIssue).where(PharmacyIPPendingIssue.id == data.issue_id)
        )
        issue = issue.scalar_one_or_none()
        if not issue:
            raise HTTPException(404, "Original IP Issue not found")

        ret_req = PharmacyIPReturn(
            request_type=data.request_type,
            issue_id=data.issue_id,
            patient_id=data.patient_id,
            patient_name=data.patient_name,
            uhid=data.uhid,
            admission_number=data.admission_number,
            ward=data.ward,
            bed_number=data.bed_number,
            status="Pending",
            requested_by=data.requested_by,
        )
        self.db.add(ret_req)
        await self.db.flush()

        for item_data in data.items:
            # Verify dispense record exists
            disp_rec = await self.db.execute(
                select(PharmacyIPDispenseRecord).where(PharmacyIPDispenseRecord.id == item_data.dispense_record_id)
            )
            if not disp_rec.scalar_one_or_none():
                raise HTTPException(400, f"Dispense record {item_data.dispense_record_id} not found")

            item = PharmacyIPReturnItem(
                return_id=ret_req.id,
                dispense_record_id=item_data.dispense_record_id,
                batch_id=item_data.batch_id,
                batch_number=item_data.batch_number,
                drug_id=item_data.drug_id,
                medication_name=item_data.medication_name,
                return_quantity=item_data.return_quantity,
                reason=item_data.reason,
                condition=item_data.condition,
                is_restockable=item_data.is_restockable,
            )
            self.db.add(item)

        await self._log(ret_req.id, "Created", None, {"requested_by": data.requested_by, "type": data.request_type})
        
        await self.db.commit()
        await self.db.refresh(ret_req)
        return ret_req

    # ── Get Returns ───────────────────────────────────────────────────
    async def list_returns(self, status: str = None) -> List[PharmacyIPReturn]:
        q = select(PharmacyIPReturn).options(
            selectinload(PharmacyIPReturn.items)
        )
        if status:
            q = q.where(PharmacyIPReturn.status == status)
        q = q.order_by(PharmacyIPReturn.request_date.desc())
        
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_return(self, return_id: uuid.UUID) -> PharmacyIPReturn:
        q = select(PharmacyIPReturn).options(
            selectinload(PharmacyIPReturn.items),
            selectinload(PharmacyIPReturn.logs),
            selectinload(PharmacyIPReturn.billing_adjustments)
        ).where(PharmacyIPReturn.id == return_id)
        
        ret = (await self.db.execute(q)).scalar_one_or_none()
        if not ret:
            raise HTTPException(404, "Return request not found")
        return ret

    # ── Process Return (By Pharmacy) ──────────────────────────────────
    async def process_return(self, return_id: uuid.UUID, data: IPReturnProcess, pharmacist_id: uuid.UUID) -> PharmacyIPReturn:
        ret = await self.get_return(return_id)
        if ret.status != "Pending":
            raise HTTPException(400, f"Cannot process return with status {ret.status}")

        if data.action not in ["Accept", "Reject"]:
            raise HTTPException(400, "Action must be Accept or Reject")

        ret.status = "Accepted" if data.action == "Accept" else "Rejected"
        ret.processed_by = pharmacist_id
        ret.processed_date = datetime.now(timezone.utc)
        ret.remarks = data.remarks

        if data.action == "Accept":
            # 1. Update Inventory for each restockable item
            for item in ret.items:
                if item.is_restockable and item.batch_id:
                    # Logic here would natively call the Inventory Engine to increment batch stock.
                    # We will log the integration event.
                    pass
            
            # 2. Add Billing Adjustment (Credit/Refund for IPD)
            if data.refund_amount_total and data.refund_amount_total > 0:
                adjustment = PharmacyIPBillingAdjustment(
                    return_id=ret.id,
                    patient_id=ret.patient_id,
                    admission_number=ret.admission_number,
                    adjustment_amount=data.refund_amount_total,
                    adjustment_type="Credit",
                    notes=data.remarks
                )
                self.db.add(adjustment)
                
                # We would also notify the central RCM Billing module to process the IPD deposit credit.

        await self._log(ret.id, f"Pharmacy {data.action}ed", pharmacist_id, {"remarks": data.remarks, "refund_amount": str(data.refund_amount_total) if data.refund_amount_total else "0"})
        await self.db.commit()
        await self.db.refresh(ret)
        return ret
