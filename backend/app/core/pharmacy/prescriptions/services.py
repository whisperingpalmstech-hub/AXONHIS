import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from .models import Prescription, PrescriptionItem
from .schemas import PrescriptionCreate

class PrescriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_prescription(self, data: PrescriptionCreate) -> Prescription:
        prescription = Prescription(
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            order_id=data.order_id,
            prescribing_doctor_id=data.prescribing_doctor_id,
            status="pending"
        )
        self.db.add(prescription)
        await self.db.flush()

        items = []
        for item_data in data.items:
            item = PrescriptionItem(
                prescription_id=prescription.id,
                drug_id=item_data.drug_id,
                dosage=item_data.dosage,
                frequency=item_data.frequency,
                duration=item_data.duration,
                instructions=item_data.instructions
            )
            self.db.add(item)
            items.append(item)
        await self.db.flush()
        prescription.items = items
        return prescription

    async def get_prescription(self, rx_id: uuid.UUID) -> Prescription:
        from sqlalchemy.orm import selectinload
        res = await self.db.execute(
            select(Prescription)
            .where(Prescription.id == rx_id)
            .options(selectinload(Prescription.items)) # Need to load items
        )
        rx = res.scalar_one_or_none()
        if not rx:
            raise HTTPException(status_code=404, detail="Prescription not found")
        return rx

    async def list_prescriptions(self, limit: int = 100) -> list[Prescription]:
        from sqlalchemy.orm import selectinload
        res = await self.db.execute(select(Prescription).options(selectinload(Prescription.items)).limit(limit))
        return list(res.scalars().all())
