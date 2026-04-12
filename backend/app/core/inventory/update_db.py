import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from app.database import engine
from sqlalchemy import text
from app.core.auth.models import User
from app.core.inventory.models import Base, Store, InventoryItem, BatchRecord, StockLedger, StoreIndent, StoreIndentItem, MaterialIssue, MaterialIssueItem, StockAdjustment, ScrapRequest

async def update_db_async():
    # Make sure we run database migration carefully
    async with engine.begin() as conn:
        print("Creating enterprise inventory tables...")
        await conn.run_sync(Base.metadata.create_all, tables=[
            Store.__table__,
            InventoryItem.__table__,
            BatchRecord.__table__,
            StockLedger.__table__,
            StoreIndent.__table__,
            StoreIndentItem.__table__,
            MaterialIssue.__table__,
            MaterialIssueItem.__table__,
            StockAdjustment.__table__,
            ScrapRequest.__table__
        ])
    print("Database schema successfully extended with Inventory and Store Management models.")

if __name__ == "__main__":
    asyncio.run(update_db_async())
