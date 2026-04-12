import asyncio
import uuid
import sys

# Must add app path
import os
sys.path.append("/app")

from app.database import AsyncSessionLocal
from app.core.linen.models import LinenCategory

async def seed():
    print("Connecting to db...")
    async with AsyncSessionLocal() as db:
        org_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        
        cats = [
            LinenCategory(name="Standard Bed Sheet", description="White cotton blend", expected_lifespan_washes=100, is_active=True, org_id=org_id),
            LinenCategory(name="Surgical Gown", description="Blue sterile", expected_lifespan_washes=50, is_active=True, org_id=org_id),
            LinenCategory(name="Patient Blanket", description="Thermal blanket", expected_lifespan_washes=200, is_active=True, org_id=org_id),
            LinenCategory(name="Pillow Cover", description="White cotton", expected_lifespan_washes=100, is_active=True, org_id=org_id),
        ]
        db.add_all(cats)
        
        try:
            await db.commit()
            print("Seeded successfully!")
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()

asyncio.run(seed())
