import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .models import (
    PharmacyInventoryBatch, PharmacyStockMovement, PharmacyItemKit,
    PharmacyInventoryAlert, PharmacyInventoryAnalysis, PharmacyInventoryLog
)
from .schemas import BatchCreate, KitCreate

class InventoryIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _log_transaction(self, user_id: uuid.UUID, txn_type: str, drug_id: Optional[uuid.UUID] = None, qty: Optional[float] = None):
        log = PharmacyInventoryLog(
            user_id=user_id,
            transaction_type=txn_type,
            drug_id=drug_id,
            quantity_change=qty
        )
        self.db.add(log)
        await self.db.commit()

    async def register_batch(self, data: BatchCreate, user_id: uuid.UUID) -> PharmacyInventoryBatch:
        batch = PharmacyInventoryBatch(**data.model_dump())
        self.db.add(batch)
        
        # Log Movement automatically
        mov = PharmacyStockMovement(
            batch_id=batch.id,
            store_id=batch.store_id,
            transaction_type="PURCHASE(REGISTER)",
            quantity_change=batch.available_quantity,
            reference_id=str(batch.id)
        )
        self.db.add(mov)
        await self.db.commit()
        await self.db.refresh(batch)
        await self._log_transaction(user_id, "BATCH_CREATED", batch.drug_id, float(batch.available_quantity))
        return batch

    async def create_kit(self, data: KitCreate, user_id: uuid.UUID) -> PharmacyItemKit:
        kit = PharmacyItemKit(
            kit_name=data.kit_name,
            description=data.description,
            kit_components=[comp.model_dump(mode='json') for comp in data.kit_components]
        )
        self.db.add(kit)
        await self.db.commit()
        await self.db.refresh(kit)
        await self._log_transaction(user_id, "KIT_CREATED")
        return kit

    async def get_kits(self) -> List[PharmacyItemKit]:
        res = await self.db.execute(select(PharmacyItemKit))
        return list(res.scalars().all())

    async def update_kit(self, kit_id: uuid.UUID, kit_components: List[dict]) -> PharmacyItemKit:
        res = await self.db.execute(select(PharmacyItemKit).where(PharmacyItemKit.id == kit_id))
        kit = res.scalar_one_or_none()
        if not kit:
            raise HTTPException(status_code=404, detail="Kit not found")
            
        kit.kit_components = kit_components
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(kit, "kit_components")
        
        await self.db.commit()
        await self.db.refresh(kit)
        return kit

    async def analyze_expiries(self):
        """Monitor medications approaching expiry dates."""
        today = datetime.now(timezone.utc).date()
        thresholds = [30, 60, 90]
        
        batches = await self.db.execute(select(PharmacyInventoryBatch))
        for batch in batches.scalars().all():
            if batch.available_quantity <= 0:
                continue
                
            days_to_expiry = (batch.expiry_date - today).days
            
            for t in thresholds:
                if 0 <= days_to_expiry <= t:
                    # check if alert already exists recently
                    existing = await self.db.execute(
                        select(PharmacyInventoryAlert).where(
                            PharmacyInventoryAlert.batch_id == batch.id,
                            PharmacyInventoryAlert.alert_type == "EXPIRY"
                        )
                    )
                    if not existing.scalar_one_or_none():
                        alert = PharmacyInventoryAlert(
                            alert_type="EXPIRY",
                            drug_id=batch.drug_id,
                            batch_id=batch.id,
                            store_id=batch.store_id,
                            message=f"Batch {batch.batch_number} expiring in {days_to_expiry} days!"
                        )
                        self.db.add(alert)
                    break # Don't alert for multiple thresholds simultaneously for same batch
        
        await self.db.commit()

    async def update_analysis(self, drug_id: uuid.UUID, abc_category: Optional[str] = None, ved_category: Optional[str] = None, is_dead_stock: Optional[int] = None):
        """ABC / VED Inventory Analysis configuration"""
        res = await self.db.execute(select(PharmacyInventoryAnalysis).where(PharmacyInventoryAnalysis.drug_id == drug_id))
        analysis = res.scalar_one_or_none()
        
        if not analysis:
            analysis = PharmacyInventoryAnalysis(drug_id=drug_id)
            self.db.add(analysis)
            
        if abc_category: analysis.abc_category = abc_category
        if ved_category: analysis.ved_category = ved_category
        if is_dead_stock is not None: analysis.is_dead_stock = is_dead_stock
        
        analysis.last_analyzed = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(analysis)
        return analysis

    async def get_alerts(self, store_id: Optional[str] = None) -> List[PharmacyInventoryAlert]:
        qs = select(PharmacyInventoryAlert)
        if store_id:
            qs = qs.where(PharmacyInventoryAlert.store_id == store_id)
        qs = qs.order_by(PharmacyInventoryAlert.alert_date.desc())
        res = await self.db.execute(qs)
        return list(res.scalars().all())

    async def get_stock_movements(self, batch_id: uuid.UUID) -> List[PharmacyStockMovement]:
        res = await self.db.execute(select(PharmacyStockMovement).where(PharmacyStockMovement.batch_id == batch_id).order_by(PharmacyStockMovement.timestamp.desc()))
        return list(res.scalars().all())
