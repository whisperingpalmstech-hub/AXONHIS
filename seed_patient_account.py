import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.append("/home/sujeetnew/Downloads/AXONHIS/backend")

from app.core.patient_portal.patient_accounts.services import PatientAccountService
from app.core.patient_portal.patient_accounts.schemas import PatientAccountCreate

async def main():
    engine = create_async_engine("postgresql+asyncpg://axonhis:changeme_in_prod@localhost:5432/axonhis")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        data = PatientAccountCreate(
            patient_id="47b82a31-0bcb-4df1-9317-e20954e6e870",
            email="suj@example.com",
            phone_number="1234567890",
            password="Password123"
        )
        try:
            account = await PatientAccountService.create_account(session, data)
            await session.commit()
            print("Successfully created patient account for suj@example.com")
        except Exception as e:
            print("Account may already exist or error occurred:", e)

asyncio.run(main())
