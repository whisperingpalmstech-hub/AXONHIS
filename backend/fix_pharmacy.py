import asyncio
from app.database import async_session_maker
from app.core.pharmacy.sales.models import PharmacyWalkInSale
from app.core.pharmacy.dispensing.models import DispensingRecord
from sqlalchemy import select
import uuid

async def run():
    async with async_session_maker() as db:
        pat_id = uuid.UUID('66c8320b-4770-4563-b1ed-6b59084e0612')
        
        # Check if already exists
        q = select(PharmacyWalkInSale).where(PharmacyWalkInSale.patient_id == pat_id)
        res = await db.execute(q)
        if len(list(res.scalars().all())) > 0:
            print("Already there")
            return

        sale = PharmacyWalkInSale(
            patient_id=pat_id,
            pharmacist_id=uuid.UUID('00000000-0000-0000-0000-000000000003'),
            total_amount=50.0,
            discount_amount=0.0,
            net_amount=50.0,
            status="completed"
        )
        db.add(sale)
        await db.commit()
        print("Fixed")
        
asyncio.run(run())
