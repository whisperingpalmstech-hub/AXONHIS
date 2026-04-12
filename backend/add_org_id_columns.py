import asyncio
from app.database import engine
from sqlalchemy import text

async def run():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN org_id UUID"))
            print("Added org_id to users")
        except Exception as e:
            print("Users:", e)
            
        try:
            await conn.execute(text("ALTER TABLE patients ADD COLUMN org_id UUID"))
            print("Added org_id to patients")
        except Exception as e:
            print("Patients:", e)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())
