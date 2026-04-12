import asyncio
from app.database import engine
from sqlalchemy import text

async def check_tables():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [r[0] for r in result]
        print("Available tables:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        # Check for AI-related tables
        ai_tables = [t for t in tables if 'ai' in t.lower() or 'summary' in t.lower()]
        print("\nAI/Summary related tables:")
        for table in sorted(ai_tables):
            print(f"  - {table}")

asyncio.run(check_tables())
