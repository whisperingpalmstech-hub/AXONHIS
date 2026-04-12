import asyncio
from app.database import AsyncSessionLocal, engine
from app.core.auth.models import User
from app.core.auth.services import hash_password
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).where(User.email == 'admin@apl-go.com'))
        if not res.scalar_one_or_none():
            u = User(
                email="admin@apl-go.com",
                password_hash=hash_password("Admin@123"),
                first_name="Apollo",
                last_name="SuperAdmin",
                phone="0000000000"
            )
            session.add(u)
            await session.commit()
            print("User was literally missing. Created it now.")
        else:
            print("User existed. Just setting pass again to be absolutely sure.")
            u = await session.execute(select(User).where(User.email == 'admin@apl-go.com'))
            u = u.scalar_one()
            u.password_hash = hash_password("Admin@123")
            await session.commit()
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())
