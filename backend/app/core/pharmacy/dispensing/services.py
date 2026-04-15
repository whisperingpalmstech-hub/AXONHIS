import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from .models import DispensingRecord
from .schemas import DispensingRecordCreate
from app.core.pharmacy.prescriptions.models import Prescription

class DispensingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def dispense_prescription(self, data: DispensingRecordCreate, user_id: uuid.UUID) -> DispensingRecord:
        from sqlalchemy.orm import selectinload
        from app.core.pharmacy.medications.models import Medication
        from app.core.pharmacy.sales.models import PharmacyWalkInSale, PharmacySaleItem

        res = await self.db.execute(select(Prescription).options(selectinload(Prescription.items)).where(Prescription.id == data.prescription_id))
        rx = res.scalar_one_or_none()
        if not rx:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        if rx.status == "dispensed":
            raise HTTPException(status_code=400, detail="Prescription already dispensed")

        rx.status = data.status
        self.db.add(rx)

        record = DispensingRecord(
            prescription_id=data.prescription_id,
            dispensed_by=user_id,
            status=data.status
        )
        self.db.add(record)
        
        # --- Create Linked Pharmacy Sale Invoice ---
        total_amount = 0.0
        sale_items = []
        
        for item in rx.items:
            med_res = await self.db.execute(select(Medication).where(Medication.id == item.drug_id))
            med = med_res.scalar_one_or_none()
            unit_price = med.unit_price if med else getattr(item, 'unit_price', 10.0)
            qty = 10.0 # Default fixed duration/dosage calculation fallback
            
            line_total = float(unit_price) * qty
            total_amount += line_total
            
            sale_items.append(PharmacySaleItem(
                drug_id=item.drug_id,
                batch_id=uuid.UUID('00000000-0000-0000-0000-000000000000'), # Default/any batch
                quantity=qty,
                unit_price=unit_price,
                total_price=line_total,
                dosage_instructions=item.instructions
            ))
            
        if total_amount > 0:
            sale = PharmacyWalkInSale(
                patient_id=rx.patient_id,
                walkin_name="Registered Patient", # Generic filler
                pharmacist_id=user_id,
                total_amount=total_amount,
                discount_amount=0.0,
                net_amount=total_amount,
                status="completed", # Auto-marked as completed/paid
                items=sale_items
            )
            self.db.add(sale)

        await self.db.flush()
        
        return record

    async def list_dispensing_records(self, limit: int = 100) -> list[DispensingRecord]:
        res = await self.db.execute(select(DispensingRecord).limit(limit))
        return list(res.scalars().all())
