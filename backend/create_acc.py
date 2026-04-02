import asyncio
import uuid
import sys
import os

# Set up app path if needed
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.core.patients.patients.models import Patient # Need this to resolve relationship
from app.core.patient_portal.patient_accounts.services import PatientAccountService
from app.core.patient_portal.patient_accounts.schemas import PatientAccountCreate

async def main():
    async with AsyncSessionLocal() as db:
        try:
            # Check if patient exists
            p_id = uuid.UUID('47b82a31-0bcb-4df1-9317-e20954e6e870')
            
            # Check if account already exists
            existing = await PatientAccountService.get_account_by_email(db, "suj@example.com")
            if not existing:
                await PatientAccountService.create_account(db, PatientAccountCreate(
                    patient_id=p_id,
                    email='suj@example.com',
                    password='Password123!',
                    phone_number=None
                ))
                await db.commit()
                print("Account created successfully")
            else:
                print("Account already exists")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
