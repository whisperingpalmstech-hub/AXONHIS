import asyncio
from app.database import engine, Base
import app.core.nursing.models # This ensures the Base registry knows about these models

async def create_tables():
    async with engine.begin() as conn:
        print("Creating Nursing Module tables explicitly...")
        await conn.run_sync(Base.metadata.create_all)
        print("Done!")

if __name__ == "__main__":
    asyncio.run(create_tables())
