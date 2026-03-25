import uuid
from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy.orm import selectinload

from .models import PharmacySalesWorklist, PharmacyPrescription, PharmacyDispensingRecord, PharmacyDispenseBatch, PharmacyDispenseLog
from .schemas import DispenseRequest

from app.core.pharmacy.inventory.models import InventoryItem
from app.core.pharmacy.batches.models import DrugBatch

class SalesWorklistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_worklists(self, status: str = None):
        q = select(PharmacySalesWorklist).options(selectinload(PharmacySalesWorklist.prescriptions))
        if status:
            q = q.where(PharmacySalesWorklist.status == status)
        q = q.order_by(PharmacySalesWorklist.created_at.desc())
        res = await self.db.execute(q)
        return list(res.scalars().all())

    async def get_worklist(self, worklist_id: uuid.UUID) -> PharmacySalesWorklist:
        q = select(PharmacySalesWorklist).options(selectinload(PharmacySalesWorklist.prescriptions)).where(PharmacySalesWorklist.id == worklist_id)
        res = await self.db.execute(q)
        wl = res.scalar_one_or_none()
        if not wl:
            raise HTTPException(status_code=404, detail="Worklist not found")
        return wl

    async def get_dispensing_logs(self, worklist_id: uuid.UUID):
        q = select(PharmacyDispenseLog).where(PharmacyDispenseLog.worklist_id == worklist_id).order_by(PharmacyDispenseLog.timestamp.desc())
        res = await self.db.execute(q)
        return list(res.scalars().all())

    async def process_dispense(self, worklist_id: uuid.UUID, data: DispenseRequest):
        wl = await self.get_worklist(worklist_id)
        if wl.status == "Completed":
            raise HTTPException(status_code=400, detail="Worklist already completed")

        records_to_add = []
        log_details_items = []

        # Validate stock and prepare records
        for item in data.items:
            # Skip stock validation if non-formulary (user bypasses inventory)
            if not item.is_non_formulary and item.drug_id:
                # 1. Aggregate validation
                q_inv = select(InventoryItem).where(InventoryItem.drug_id == item.drug_id)
                inv = (await self.db.execute(q_inv)).scalar_one_or_none()
                if not inv or inv.quantity_available < item.quantity_dispensed:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock for {item.medication_name}")
                
                # 2. Batch validation
                for b in item.batches:
                    q_batch = select(DrugBatch).where(DrugBatch.id == b.batch_id, DrugBatch.drug_id == item.drug_id)
                    batch = (await self.db.execute(q_batch)).scalar_one_or_none()
                    if not batch or batch.quantity < b.quantity:
                        raise HTTPException(status_code=400, detail=f"Insufficient stock in batch {b.batch_number} for {item.medication_name}")

            total_price = Decimal(str(item.quantity_dispensed)) * Decimal(str(item.unit_price))
            
            # Create dispense record
            record = PharmacyDispensingRecord(
                worklist_id=worklist_id,
                prescription_id=item.prescription_id,
                drug_id=item.drug_id,
                medication_name=item.medication_name,
                quantity_dispensed=item.quantity_dispensed,
                dosage_instructions=item.dosage_instructions,
                unit_price=item.unit_price,
                total_price=total_price,
                dispensed_by=uuid.UUID(data.pharmacist_id)
            )
            
            # Create batch dispense records
            for b in item.batches:
                record.batches.append(PharmacyDispenseBatch(
                    batch_id=b.batch_id,
                    batch_number=b.batch_number,
                    quantity=b.quantity,
                    expiry_date=b.expiry_date
                ))
            
            records_to_add.append(record)
            
            log_details_items.append({
                "medication": item.medication_name,
                "qty": str(item.quantity_dispensed),
                "total": str(total_price),
                "is_substitute": bool(item.substituted_for),
                "original_med": item.substituted_for
            })

        # Deduct stock
        for item in data.items:
            if not item.is_non_formulary and item.drug_id:
                q_inv = select(InventoryItem).where(InventoryItem.drug_id == item.drug_id)
                inv = (await self.db.execute(q_inv)).scalar_one()
                inv.quantity_available -= Decimal(str(item.quantity_dispensed))

                for b in item.batches:
                    q_batch = select(DrugBatch).where(DrugBatch.id == b.batch_id)
                    batch = (await self.db.execute(q_batch)).scalar_one()
                    batch.quantity -= Decimal(str(b.quantity))

        for rec in records_to_add:
            self.db.add(rec)
            
        wl.status = "Completed"

        # Audit Trail
        log = PharmacyDispenseLog(
            worklist_id=worklist_id,
            pharmacist_id=uuid.UUID(data.pharmacist_id),
            action_type="PRESCRIPTION_DISPENSED",
            billing_transaction_id=data.billing_transaction_id,
            details={"items": log_details_items}
        )
        self.db.add(log)
        
        await self.db.commit()
        await self.db.refresh(wl)
        return wl

    async def mock_seed_worklist(self):
        # Quick helper to mock some data if needed.
        wl = PharmacySalesWorklist(
            patient_name="Rahul Sharma",
            uhid="UHID1234",
            doctor_name="Dr. Mehta",
            prescription_id=uuid.uuid4(),
            status="Pending"
        )
        p1 = PharmacyPrescription(
            worklist_item=wl,
            medication_name="Amoxicillin 500mg",
            dosage_instructions="1 tablet twice a day",
            quantity_prescribed=10
        )
        p2 = PharmacyPrescription(
            worklist_item=wl,
            medication_name="Paracetamol 650mg",
            dosage_instructions="1 tablet SOS",
            quantity_prescribed=5
        )
        self.db.add(wl)
        self.db.add(p1)
        self.db.add(p2)
        await self.db.commit()
        return wl
