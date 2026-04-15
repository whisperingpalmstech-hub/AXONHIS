import asyncio
from app.database import async_session_maker
from app.core.axonhis_md.models import Practitioner
from cryptography.fernet import Fernet
import uuid

async def seed_doctor():
    async with async_session_maker() as db:
        docs = await db.execute("SELECT id FROM practitioners WHERE email = 'doc1@axonhis.local'")
        if list(docs):
            print("Doctor already exists")
            return
            
        doc = Practitioner(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            first_name="Dr. John",
            last_name="Doe",
            email="doc1@axonhis.local",
            specialty="General Medicine",
            license_number="LIC12345",
            status="active"
        )
        db.add(doc)
        await db.commit()
        print("Doctor added! Name: Dr. John Doe, Email: doc1@axonhis.local")

if __name__ == "__main__":
    asyncio.run(seed_doctor())
