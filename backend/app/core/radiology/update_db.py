import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from app.database import engine
from sqlalchemy import text
from app.core.auth.models import User # this will register 'users' table in metadata before creating radiology models
from app.core.radiology.radiology_reports.models import Base

async def update_db_async():
    async with engine.connect() as conn:
        # Extend status length and clinical notes
        await conn.execute(text("ALTER TABLE radiology_reports ALTER COLUMN status TYPE VARCHAR(30);"))
        await conn.execute(text("ALTER TABLE radiology_reports ADD COLUMN IF NOT EXISTS clinical_notes TEXT;"))
        await conn.execute(text("ALTER TABLE radiology_reports ADD COLUMN IF NOT EXISTS conclusion TEXT;"))
        await conn.commit()
    
    async with engine.begin() as conn:
        # Create the new tables
        await conn.run_sync(Base.metadata.create_all, tables=[
            Base.metadata.tables['radiology_templates'],
            Base.metadata.tables['radiology_validations'],
            Base.metadata.tables['radiology_amendment_logs']
        ])
    
    print("Radiology database schema updated successfully.")

if __name__ == "__main__":
    asyncio.run(update_db_async())
