import bcrypt
import asyncio
from sqlalchemy import update
from app.database import AsyncSessionLocal
from app.core.patients.patients.models import Patient
from app.core.patient_portal.patient_accounts.models import PatientAccount

async def fix_pw():
    salt = bcrypt.gensalt(rounds=12)
    hash_val = bcrypt.hashpw(b"Password123!", salt).decode("utf-8")
    async with AsyncSessionLocal() as session:
        await session.execute(update(PatientAccount).where(PatientAccount.email=="suj@example.com").values(password_hash=hash_val))
        await session.commit()
    print("FIXED", hash_val)

if __name__ == "__main__":
    asyncio.run(fix_pw())
