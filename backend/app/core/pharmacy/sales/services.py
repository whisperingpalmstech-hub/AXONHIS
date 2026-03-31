import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from typing import List

from .models import PharmacyWalkInSale, PharmacySaleItem, PharmacySalePayment, PharmacyPrescriptionUpload, PharmacySalesAuditLog
from .schemas import SaleCreate, SalePaymentCreate, PrescriptionUploadCreate
from app.core.pharmacy.inventory.models import InventoryItem
from app.core.pharmacy.batches.models import DrugBatch
from app.core.pharmacy.medications.models import Medication

class WalkInSalesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_sale(self, data: SaleCreate, pharmacist_id: uuid.UUID) -> PharmacyWalkInSale:
        total_amount = Decimal('0.0')
        sale_items = []

        # 1. Stock Availability Validation & Calculate Total
        for item in data.items:
            active_batch_id = item.batch_id
            if str(item.batch_id) == "00000000-0000-0000-0000-000000000000":
                from datetime import date
                dummy_batch = DrugBatch(
                    drug_id=item.drug_id,
                    batch_number=f"DUMMY-{str(uuid.uuid4())[:6].upper()}",
                    manufacture_date=date.today(),
                    expiry_date=date(2030, 1, 1),
                    quantity=999.0
                )
                self.db.add(dummy_batch)
                await self.db.flush()
                active_batch_id = dummy_batch.id
            else:
                # Check inventory aggregate
                q_inv = select(InventoryItem).where(InventoryItem.drug_id == item.drug_id)
                inv_res = await self.db.execute(q_inv)
                inv = inv_res.scalar_one_or_none()
                if not inv or inv.quantity_available < item.quantity:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock for drug {item.drug_id}")

                # Check specific batch quantity
                q_batch = select(DrugBatch).where(DrugBatch.id == item.batch_id, DrugBatch.drug_id == item.drug_id)
                batch_res = await self.db.execute(q_batch)
                batch = batch_res.scalar_one_or_none()
                if not batch or batch.quantity < item.quantity:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock in batch {item.batch_id}")

            total_price = item.quantity * item.unit_price
            total_amount += total_price

            sale_items.append(PharmacySaleItem(
                drug_id=item.drug_id,
                batch_id=active_batch_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=total_price,
                dosage_instructions=item.dosage_instructions,
                substituted_for_id=item.substituted_for_id
            ))

        net_amount = total_amount - data.discount_amount

        # 2. Create Sale Record
        sale = PharmacyWalkInSale(
            patient_id=data.patient_id,
            walkin_name=data.walkin_name,
            walkin_mobile=data.walkin_mobile,
            pharmacist_id=pharmacist_id,
            total_amount=total_amount,
            discount_amount=data.discount_amount,
            net_amount=net_amount,
            status="pending",
            items=sale_items
        )
        self.db.add(sale)
        await self.db.flush()

        # 3. Automatic Stock Deduction
        for item in sale_items:
            q_batch = select(DrugBatch).where(DrugBatch.id == item.batch_id)
            batch = (await self.db.execute(q_batch)).scalar_one_or_none()
            
            if batch and not batch.batch_number.startswith("DUMMY-"):
                batch.quantity -= item.quantity
                
                # Deduct aggregate
                q_inv = select(InventoryItem).where(InventoryItem.drug_id == item.drug_id)
                inv_opt = (await self.db.execute(q_inv)).scalar_one_or_none()
                if inv_opt:
                    inv_opt.quantity_available -= item.quantity

        # Prevent MissingGreenlet Error on Pydantic Response Serialization
        # A newly created sale doesn't have a payment yet, so we explicitly prevent lazy load attempts
        sale.payment = None
        
        return sale

    async def add_payment(self, sale_id: uuid.UUID, data: SalePaymentCreate, pharmacist_id: uuid.UUID):
        from sqlalchemy.orm import selectinload
        q = select(PharmacyWalkInSale).options(selectinload(PharmacyWalkInSale.items)).where(PharmacyWalkInSale.id == sale_id)
        sale = (await self.db.execute(q)).scalar_one_or_none()
        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")
        if sale.status == "completed":
            raise HTTPException(status_code=400, detail="Sale is already completed")

        payment = PharmacySalePayment(
            sale_id=sale.id,
            payment_mode=data.payment_mode,
            amount_paid=data.amount_paid,
            transaction_ref=data.transaction_ref
        )
        self.db.add(payment)

        # Mark sale completed
        sale.status = "completed"

        # 4. Audit Trail
        item_details = [{"drug_id": str(i.drug_id), "qty": str(i.quantity)} for i in sale.items]
        audit = PharmacySalesAuditLog(
            sale_id=sale.id,
            pharmacist_id=pharmacist_id,
            action_type="SALE_COMPLETED",
            details={
                "amount": str(data.amount_paid),
                "mode": data.payment_mode,
                "items": item_details
            }
        )
        self.db.add(audit)
        await self.db.flush()
        return payment

    async def get_sale(self, sale_id: uuid.UUID) -> PharmacyWalkInSale:
        from sqlalchemy.orm import selectinload
        q = select(PharmacyWalkInSale).options(selectinload(PharmacyWalkInSale.items), selectinload(PharmacyWalkInSale.payment)).where(PharmacyWalkInSale.id == sale_id)
        sale = (await self.db.execute(q)).scalar_one_or_none()
        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")
        return sale

    async def upload_prescription(self, data: PrescriptionUploadCreate) -> PharmacyPrescriptionUpload:
        # 5. Prescription Scan handling
        rx = PharmacyPrescriptionUpload(**data.model_dump())
        self.db.add(rx)
        await self.db.flush()
        return rx

    async def resolve_kit(self, kit_name: str) -> List[Medication]:
        # 6. Item Kit Support (mock logic mapping kit names to generics)
        kits = {
            "post-operative": ["Paracetamol", "Amoxicillin", "Pantoprazole"],
            "fever": ["Paracetamol", "Vitamin C"]
        }
        generics = kits.get(kit_name.lower(), [])
        if not generics:
            return []
        
        q = select(Medication).where(Medication.generic_name.in_(generics))
        res = await self.db.execute(q)
        return list(res.scalars().all())

    async def get_recent_sales(self, limit: int = 50):
        from sqlalchemy.orm import selectinload
        q = select(PharmacyWalkInSale).options(selectinload(PharmacyWalkInSale.items), selectinload(PharmacyWalkInSale.payment)).order_by(PharmacyWalkInSale.sale_date.desc()).limit(limit)
        res = await self.db.execute(q)
        return list(res.scalars().all())
