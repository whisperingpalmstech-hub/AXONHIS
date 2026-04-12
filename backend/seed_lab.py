import asyncio
import uuid
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from app.database import AsyncSessionLocal
from sqlalchemy import text

async def seed_lab():
    async with AsyncSessionLocal() as db:
        # Get a patient ID (any existing)
        res = await db.execute(text("SELECT id FROM patients LIMIT 1"))
        patient_row = res.fetchone()
        if not patient_row:
            print("No patients exist.")
            return
        patient_id = patient_row[0]

        # Get an order ID (any existing)
        res = await db.execute(text("SELECT id FROM orders LIMIT 1"))
        order_row = res.fetchone()
        if not order_row:
            print("No orders exist.")
            return
        order_id = order_row[0]
        
        # Get encounter ID
        res = await db.execute(text("SELECT id FROM encounters LIMIT 1"))
        enc_row = res.fetchone()
        if not enc_row:
            print("No encounters exist.")
            return
        enc_id = enc_row[0]

        # create a LabOrder
        lab_order_id = uuid.uuid4()
        await db.execute(text(f"""
            INSERT INTO lab_orders (id, order_id, patient_id, encounter_id, status, ordered_at)
            VALUES ('{lab_order_id}', '{order_id}', '{patient_id}', '{enc_id}', 'PROCESSING', NOW())
        """))

        # create a LabSample in PROCESSING state
        sample_id = uuid.uuid4()
        barcode = f"SMP-{str(sample_id)[:8].upper()}"
        await db.execute(text(f"""
            INSERT INTO lab_samples (id, lab_order_id, sample_barcode, sample_type, status, collection_time, received_at, is_outsourced)
            VALUES ('{sample_id}', '{lab_order_id}', '{barcode}', 'blood', 'PROCESSING', NOW(), NOW(), false)
        """))

        await db.commit()
        print(f"Success! Mock sample {barcode} created in PROCESSING state.")

if __name__ == "__main__":
    asyncio.run(seed_lab())
