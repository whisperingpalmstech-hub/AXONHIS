import asyncio
from app.database import engine
from app.core.administration.tenants.models import Base

async def init_db():
    async with engine.begin() as conn:
        from app.core.administration.tenants.models import OrganizationEntity, FacilitySite
        # Creates all tables extending Base that don't exist yet
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_db())
