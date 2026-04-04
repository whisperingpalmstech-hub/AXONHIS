import asyncio
from app.database import engine, Base
from app.core.auth.models import User
from app.core.inventory.models import Store, InventoryItem
from app.core.procurement.models import *

async def init_db():
    async with engine.begin() as conn:
        print("Creating Procurement tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Done.")

if __name__ == "__main__":
    asyncio.run(init_db())
