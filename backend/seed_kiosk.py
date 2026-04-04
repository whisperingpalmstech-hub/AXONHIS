import asyncio
from app.database import engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.kiosk.models import TokenQueue, QueueCounter

async def seed_kiosk():
    async with AsyncSession(engine) as db:
        
        # Ensure we have a counter
        res = await db.execute(select(QueueCounter).limit(1))
        counter = res.scalars().first()
        if not counter:
            counter = QueueCounter(counter_name="Counter 3", department="General OPD")
            db.add(counter)
            await db.flush()

        # Check if queue already has data
        res = await db.execute(select(TokenQueue))
        existing_tokens = res.scalars().all()
        
        if not existing_tokens:
            print("Seeding live hospital tokens...")
            tokens = [
                # Emergency
                TokenQueue(token_number=1, token_prefix="ER", token_display="ER-001", department="Cardiology", patient_name="John Doe", status="Pending", priority=True, priority_reason="Chest Pain", counter_id=counter.id),
                # General walk-ins
                TokenQueue(token_number=2, token_prefix="T", token_display="T-002", department="General OPD", patient_name="Alice Smith", status="Pending", priority=False),
                TokenQueue(token_number=3, token_prefix="T", token_display="T-003", department="Orthopedics", patient_uhid="UHID-X891", patient_name="Bob Jones", status="Pending", priority=False),
                # One person already being called
                TokenQueue(token_number=4, token_prefix="T", token_display="T-004", department="Pediatrics", patient_name="Little Timmy", status="Calling", priority=False, counter_id=counter.id),
                # No Show
                TokenQueue(token_number=5, token_prefix="T", token_display="T-005", department="General OPD", status="No Show", priority=False)
            ]
            
            for t in tokens:
                db.add(t)
            await db.commit()
            print("Live token data injected successfully!")
        else:
            print("Data already exists in queue.")

if __name__ == "__main__":
    asyncio.run(seed_kiosk())
