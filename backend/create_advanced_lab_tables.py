import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, Base
# Import all models to attach to Base
from app.core.advanced_lab.models import *

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

if __name__ == "__main__":
    asyncio.run(create_tables())
