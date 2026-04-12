import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from app.database import engine
from sqlalchemy import text
from app.core.lab.models import Base

async def update_db_async():
    async with engine.connect() as conn:
        await conn.execute(text("ALTER TABLE lab_tests ADD COLUMN IF NOT EXISTS is_calculated BOOLEAN DEFAULT FALSE NOT NULL;"))
        await conn.execute(text("ALTER TABLE lab_tests ADD COLUMN IF NOT EXISTS calculation_formula VARCHAR(500);"))
        await conn.execute(text("ALTER TABLE lab_samples ADD COLUMN IF NOT EXISTS is_outsourced BOOLEAN DEFAULT FALSE NOT NULL;"))
        await conn.execute(text("ALTER TABLE lab_samples ADD COLUMN IF NOT EXISTS outsourced_to VARCHAR(200);"))
        await conn.execute(text("ALTER TABLE lab_samples ADD COLUMN IF NOT EXISTS outsourced_date TIMESTAMP WITH TIME ZONE;"))
        await conn.commit()
    
    # Create the single new table if it doesn't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[Base.metadata.tables['lab_reagent_consumption']])
    
    print("Lab database schema updated successfully.")

if __name__ == "__main__":
    asyncio.run(update_db_async())
