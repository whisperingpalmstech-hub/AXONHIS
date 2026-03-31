import asyncio
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker
from app.core.pharmacy.medications.models import Medication
from app.core.pharmacy.inventory.models import InventoryItem
from app.core.pharmacy.batches.models import DrugBatch

async def seed():
    async with async_session_maker() as db:
        drugs = [
            {"name": "Paracetamol", "generic": "Acetaminophen", "code": "DRG-001", "strength": "500mg", "form": "Tablet", "price": 10.00},
            {"name": "Amoxicillin", "generic": "Amoxicillin", "code": "DRG-002", "strength": "500mg", "form": "Capsule", "price": 50.00},
            {"name": "Ibuprofen", "generic": "Ibuprofen", "code": "DRG-003", "strength": "400mg", "form": "Tablet", "price": 15.00},
        ]
        
        for d in drugs:
            med = Medication(
                drug_name=d["name"],
                generic_name=d["generic"],
                drug_code=d["code"],
                strength=d["strength"],
                form=d["form"],
                manufacturer="PharmaCorp",
                category="General",
                package_size="10s",
                is_active=True
            )
            db.add(med)
            await db.flush()
            
            inv = InventoryItem(
                drug_id=med.id,
                quantity_available=1000,
                reorder_level=100,
                reorder_quantity=500,
                location="Main Pharmacy",
                cost_price=Decimal("5.00"),
                unit_price=Decimal(str(d["price"]))
            )
            db.add(inv)
            
            batch = DrugBatch(
                drug_id=med.id,
                batch_number=f"BCH-{d['name'].upper()}-001",
                quantity=1000,
                cost_price=Decimal("5.00"),
                unit_price=Decimal(str(d["price"])),
                expiry_date="2026-12-31"
            )
            db.add(batch)
            
        await db.commit()
        print("Pharmacy DB seeded.")

if __name__ == "__main__":
    asyncio.run(seed())
