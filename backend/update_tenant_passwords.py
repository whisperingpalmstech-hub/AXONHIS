import asyncio
from sqlalchemy import update
from app.database import engine
from app.core.auth.models import User
from app.core.auth.services import hash_password

async def run():
    async with engine.begin() as conn:
        new_hash = hash_password("Admin@123")
        stmt = update(User).where(User.email.like('admin@%')).values(password_hash=new_hash)
        await conn.execute(stmt)

if __name__ == "__main__":
    asyncio.run(run())
