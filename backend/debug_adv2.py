from app.database import AsyncSessionLocal
from app.core.advanced_lab.models import HistoSpecimen, HistoBlock
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
import asyncio

async def test():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(HistoSpecimen).options(joinedload(HistoSpecimen.blocks).joinedload(HistoBlock.slides)))
        print("RESULTS:", res.unique().scalars().all())

asyncio.run(test())
