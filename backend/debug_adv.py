from app.database import AsyncSessionLocal
from app.core.advanced_lab.models import HistoSpecimen
from sqlalchemy.future import select
import asyncio

async def test():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(HistoSpecimen))
        print("RESULTS:", res.scalars().all())

asyncio.run(test())
