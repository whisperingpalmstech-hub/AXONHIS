import asyncio
import os
import sys

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://AxonicHIS:SecurePassword123!@localhost:5432/axonhis")

async def run_fix():
    print(f"Connecting to {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE ipd_admission_records ALTER COLUMN admitting_doctor TYPE VARCHAR USING admitting_doctor::VARCHAR;"))
        print("Success")

asyncio.run(run_fix())
