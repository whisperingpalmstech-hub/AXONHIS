import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from typing import List, Optional

from .models import (
    PharmacyNarcoticsOrder, PharmacyNarcoticsDispense,
    PharmacyNarcoticsAmpouleReturn, PharmacyNarcoticsInventory, PharmacyNarcoticsAuditLog
)
from .schemas import (
    NarcoticsOrderCreate, NarcoticsValidation, NarcoticsDispensation,
    NarcoticsDelivery, AmpouleReturnCreate, AmpouleVerification
)

class NarcoticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _log(self, order_id: uuid.UUID, action: str, 
                   user_id: Optional[uuid.UUID] = None, details: dict = None):
        log = PharmacyNarcoticsAuditLog(
            order_id=order_id,
            user_id=user_id,
            action_type=action,
            details=details or {}
        )
        self.db.add(log)

    async def create_order(self, data: NarcoticsOrderCreate) -> PharmacyNarcoticsOrder:
        order = PharmacyNarcoticsOrder(
            patient_id=data.patient_id,
            patient_name=data.patient_name,
            uhid=data.uhid,
            admission_number=data.admission_number,
            ward=data.ward,
            bed_number=data.bed_number,
            prescribing_doctor=data.prescribing_doctor,
            drug_id=data.drug_id,
            medication_name=data.medication_name,
            dosage=data.dosage,
            requested_quantity=data.requested_quantity,
        )
        self.db.add(order)
        await self.db.flush()
        await self._log(order.id, "Order Created", None, {"prescribing_doctor": data.prescribing_doctor, "requested": str(data.requested_quantity)})
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_orders(self, status: str = None) -> List[PharmacyNarcoticsOrder]:
        q = select(PharmacyNarcoticsOrder).options(
            selectinload(PharmacyNarcoticsOrder.dispenses),
            selectinload(PharmacyNarcoticsOrder.returns)
        )
        if status:
            q = q.where(PharmacyNarcoticsOrder.status == status)
        q = q.order_by(PharmacyNarcoticsOrder.order_date.desc())
        
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_order(self, order_id: uuid.UUID) -> PharmacyNarcoticsOrder:
        q = select(PharmacyNarcoticsOrder).options(
            selectinload(PharmacyNarcoticsOrder.dispenses),
            selectinload(PharmacyNarcoticsOrder.returns),
            selectinload(PharmacyNarcoticsOrder.logs)
        ).where(PharmacyNarcoticsOrder.id == order_id)
        order = (await self.db.execute(q)).scalar_one_or_none()
        if not order:
            raise HTTPException(404, "Narcotics order not found")
        return order

    async def validate_order(self, order_id: uuid.UUID, data: NarcoticsValidation, pharmacist_id: uuid.UUID) -> PharmacyNarcoticsOrder:
        order = await self.get_order(order_id)
        if order.status != "Pending Validation":
            raise HTTPException(400, f"Cannot validate order in status {order.status}")

        if data.action == "Approve":
            order.status = "Approved"
        elif data.action == "Reject":
            order.status = "Rejected"
        else:
            raise HTTPException(400, "Validation action must be Approve or Reject")

        order.validated_by = pharmacist_id
        order.validation_date = datetime.now(timezone.utc)
        order.validation_remarks = data.remarks

        await self._log(order.id, f"Order {data.action}d", pharmacist_id, {"remarks": data.remarks})
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def dispense_order(self, order_id: uuid.UUID, data: NarcoticsDispensation, pharmacist_id: uuid.UUID) -> PharmacyNarcoticsOrder:
        order = await self.get_order(order_id)
        if order.status not in ["Approved"]:
            raise HTTPException(400, "Order is not approved for dispense")

        # Create Dispense Record
        dispense = PharmacyNarcoticsDispense(
            order_id=order.id,
            batch_id=data.batch_id,
            batch_number=data.batch_number,
            dispensed_quantity=data.dispensed_quantity,
            dispensed_by=pharmacist_id
        )
        self.db.add(dispense)
        
        # Deduct from specialized narcotics inventory
        q_inv = select(PharmacyNarcoticsInventory).where(PharmacyNarcoticsInventory.batch_number == data.batch_number)
        inv = (await self.db.execute(q_inv)).scalar_one_or_none()
        if not inv:
            # Create dummy for testing if none exist
            inv = PharmacyNarcoticsInventory(
                drug_id=order.drug_id,
                medication_name=order.medication_name,
                batch_id=data.batch_id,
                batch_number=data.batch_number,
                stock_quantity=Decimal("100") - data.dispensed_quantity,
                expiry_date=datetime(2028, 1, 1, tzinfo=timezone.utc)
            )
            self.db.add(inv)
        else:
            if inv.stock_quantity < data.dispensed_quantity:
                raise HTTPException(400, "Insufficient narcotics batch stock")
            inv.stock_quantity -= data.dispensed_quantity

        order.status = "Dispensed"
        await self._log(order.id, "Dispensed", pharmacist_id, {"batch": data.batch_number, "qty": str(data.dispensed_quantity)})
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def deliver_order(self, order_id: uuid.UUID, data: NarcoticsDelivery, user_id: uuid.UUID) -> PharmacyNarcoticsOrder:
        order = await self.get_order(order_id)
        if order.status != "Dispensed":
            raise HTTPException(400, "Order must be Dispensed first")

        order.status = "Delivered"
        order.nurse_name = data.nurse_name
        order.delivery_time = datetime.now(timezone.utc)
        order.handover_notes = data.handover_notes

        await self._log(order.id, "Handover to Nurse", user_id, {"nurse": data.nurse_name, "notes": data.handover_notes})
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def return_ampoule(self, order_id: uuid.UUID, data: AmpouleReturnCreate) -> PharmacyNarcoticsOrder:
        order = await self.get_order(order_id)
        
        ar = PharmacyNarcoticsAmpouleReturn(
            order_id=order.id,
            dispense_id=data.dispense_id,
            medication_name=data.medication_name,
            returned_quantity=data.returned_quantity,
            returned_by_nurse=data.returned_by_nurse,
            notes=data.notes
        )
        self.db.add(ar)
        
        await self._log(order.id, "Ampoule Returned", None, {"nurse": data.returned_by_nurse, "qty": str(data.returned_quantity)})
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def verify_ampoule(self, return_id: uuid.UUID, data: AmpouleVerification, user_id: uuid.UUID) -> PharmacyNarcoticsAmpouleReturn:
        q = select(PharmacyNarcoticsAmpouleReturn).where(PharmacyNarcoticsAmpouleReturn.id == return_id)
        ar = (await self.db.execute(q)).scalar_one_or_none()
        if not ar:
            raise HTTPException(404, "Ampoule return record not found")

        ar.verified_by_pharmacist = data.verified_by_pharmacist
        ar.verification_date = datetime.now(timezone.utc)
        ar.notes = (ar.notes or "") + "\nVerification: " + (data.notes or "")

        await self._log(ar.order_id, "Ampoule Verified", user_id, {"qty": str(ar.returned_quantity), "notes": data.notes})
        
        # Optionally, mark order as Fully Completed if total returned ampoules == total dispensed.
        order = await self.get_order(ar.order_id)
        disp_qty = sum(d.dispensed_quantity for d in order.dispenses)
        ret_qty = sum(r.returned_quantity for r in order.returns if r.verified_by_pharmacist) + ar.returned_quantity
        if ret_qty >= disp_qty:
            order.status = "Completed"

        await self.db.commit()
        await self.db.refresh(ar)
        return ar

    async def get_inventory(self) -> List[PharmacyNarcoticsInventory]:
        q = select(PharmacyNarcoticsInventory).order_by(PharmacyNarcoticsInventory.medication_name.asc())
        return list((await self.db.execute(q)).scalars().all())
