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
        res = await self.db.execute(select(Prescription).where(Prescription.id == data.prescription_id))
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
        await self.db.flush()
        
        return record

    async def list_dispensing_records(self, limit: int = 100) -> list[DispensingRecord]:
        res = await self.db.execute(select(DispensingRecord).limit(limit))
        return list(res.scalars().all())
