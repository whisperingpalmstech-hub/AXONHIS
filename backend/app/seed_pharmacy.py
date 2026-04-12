import asyncio
import uuid
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.core.pharmacy.medications.models import Medication
from app.core.pharmacy.inventory.models import InventoryItem
from app.core.pharmacy.batches.models import DrugBatch
from datetime import date, timedelta

MOCK_MEDICATIONS = [
    {
        "drug_code": "M001",
        "drug_name": "Paracetamol 500mg",
        "generic_name": "Paracetamol",
        "drug_class": "Analgesic",
        "form": "Tablet",
        "strength": "500mg",
        "manufacturer": "PharmaCorp",
        "qty": 500.0
    },
    {
        "drug_code": "M002",
        "drug_name": "Amoxicillin 500mg",
        "generic_name": "Amoxicillin",
        "drug_class": "Antibiotic",
        "form": "Capsule",
        "strength": "500mg",
        "manufacturer": "BioHealth",
        "qty": 200.0
    },
    {
        "drug_code": "M003",
        "drug_name": "Ceftriaxone 1g",
        "generic_name": "Ceftriaxone",
        "drug_class": "Antibiotic",
        "form": "Injection",
        "strength": "1g",
        "manufacturer": "BioHealth",
        "qty": 50.0
    },
    {
        "drug_code": "M004",
        "drug_name": "Metformin 500mg",
        "generic_name": "Metformin",
        "drug_class": "Antidiabetic",
        "form": "Tablet",
        "strength": "500mg",
        "manufacturer": "DiabCare",
        "qty": 1000.0
    }
]

async def seed_pharmacy() -> None:
    async with AsyncSessionLocal() as db:
        for med_data in MOCK_MEDICATIONS:
            res = await db.execute(select(Medication).where(Medication.drug_code == med_data["drug_code"]))
            med = res.scalar_one_or_none()
            if not med:
                med = Medication(
                    drug_code=med_data["drug_code"],
                    drug_name=med_data["drug_name"],
                    generic_name=med_data["generic_name"],
                    drug_class=med_data["drug_class"],
                    form=med_data["form"],
                    strength=med_data["strength"],
                    manufacturer=med_data["manufacturer"]
                )
                db.add(med)
                await db.flush()
                
                # add inventory
                inv = InventoryItem(
                    drug_id=med.id,
                    quantity_available=med_data["qty"],
                    reorder_threshold=50.0
                )
                db.add(inv)
                
                # add batch
                batch = DrugBatch(
                    drug_id=med.id,
                    batch_number=f"BATCH-{med.drug_code}-2026",
                    manufacture_date=date.today() - timedelta(days=30),
                    expiry_date=date.today() + timedelta(days=365),
                    quantity=med_data["qty"]
                )
                db.add(batch)
                
        await db.commit()
        print("Pharmacy seeded!")

if __name__ == "__main__":
    asyncio.run(seed_pharmacy())
