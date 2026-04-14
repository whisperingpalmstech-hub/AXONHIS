"""Stock Valuation Services for Inventory."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.core.inventory.valuation.models import (
    StockValuation, StockValuationItem, ValuationMethod, StockAdjustment
)
from app.core.inventory.valuation.schemas import (
    ValuationMethodCreate, StockValuationRequest, StockAdjustmentCreate
)


class ValuationService:
    """Service for stock valuation operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_valuation_method(self, method_data: ValuationMethodCreate) -> ValuationMethod:
        """Create a valuation method."""
        method = ValuationMethod(**method_data.model_dump())
        self.db.add(method)
        await self.db.commit()
        await self.db.refresh(method)
        return method
    
    async def calculate_stock_value(
        self, request: StockValuationRequest, created_by: str
    ) -> StockValuation:
        """Calculate stock value using specified method."""
        # Generate valuation number
        result = await self.db.execute(select(func.max(StockValuation.id)))
        max_id = result.scalar()
        valuation_number = f"VAL-{datetime.now().strftime('%Y%m%d')}-{(max_id or 0) + 1:04d}"
        
        # Get inventory items
        from app.core.inventory.models import InvItem, BatchRecord
        query = select(InvItem, BatchRecord).join(
            BatchRecord, InvItem.id == BatchRecord.item_id
        )
        
        if request.store_id:
            query = query.where(BatchRecord.store_id == request.store_id)
        
        result = await self.db.execute(query)
        items = result.all()
        
        total_value = 0.0
        total_quantity = 0.0
        valuation_items = []
        
        for item, batch in items:
            quantity = batch.quantity or 0
            unit_cost = batch.purchase_price or 0
            total_cost = quantity * unit_cost
            
            total_value += total_cost
            total_quantity += quantity
            
            valuation_items.append(StockValuationItem(
                item_id=item.id,
                batch_record_id=batch.id,
                quantity=quantity,
                unit_cost=unit_cost,
                total_cost=total_cost,
                valuation_method=request.valuation_method
            ))
        
        # Create valuation record
        valuation = StockValuation(
            valuation_number=valuation_number,
            store_id=request.store_id,
            valuation_method=request.valuation_method,
            valuation_date=datetime.now(timezone.utc),
            total_value=total_value,
            total_quantity=total_quantity,
            created_by=created_by
        )
        self.db.add(valuation)
        await self.db.flush()
        
        # Add valuation items
        for item in valuation_items:
            item.valuation_id = valuation.id
            self.db.add(item)
        
        await self.db.commit()
        await self.db.refresh(valuation)
        return valuation
    
    async def create_stock_adjustment(self, adjustment_data: StockAdjustmentCreate, approved_by: str) -> StockAdjustment:
        """Create a stock adjustment."""
        # Generate adjustment number
        result = await self.db.execute(select(func.max(StockAdjustment.id)))
        max_id = result.scalar()
        adjustment_number = f"ADJ-{datetime.now().strftime('%Y%m%d')}-{(max_id or 0) + 1:04d}"
        
        adjustment = StockAdjustment(
            **adjustment_data.model_dump(),
            adjustment_number=adjustment_number,
            approved_by=approved_by
        )
        self.db.add(adjustment)
        await self.db.commit()
        await self.db.refresh(adjustment)
        return adjustment
    
    async def get_store_valuation(self, store_id: str, valuation_date: datetime) -> Optional[StockValuation]:
        """Get valuation for a store on a specific date."""
        result = await self.db.execute(
            select(StockValuation).where(
                StockValuation.store_id == store_id,
                StockValuation.valuation_date <= valuation_date
            ).order_by(StockValuation.valuation_date.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_item_valuation(self, item_id: str, valuation_date: datetime) -> List[Dict[str, Any]]:
        """Get valuation for an item."""
        result = await self.db.execute(
            select(StockValuationItem).join(
                StockValuation, StockValuationItem.valuation_id == StockValuation.id
            ).where(
                StockValuationItem.item_id == item_id,
                StockValuation.valuation_date <= valuation_date
            ).order_by(StockValuation.valuation_date.desc())
        )
        items = result.scalars().all()
        
        return [
            {
                "item_id": str(item.item_id),
                "batch_record_id": str(item.batch_record_id),
                "quantity": float(item.quantity),
                "unit_cost": float(item.unit_cost),
                "total_cost": float(item.total_cost),
                "valuation_method": item.valuation_method
            }
            for item in items
        ]
    
    async def calculate_fifo_value(self, item_id: str, store_id: Optional[str] = None) -> float:
        """Calculate FIFO value for an item."""
        from app.core.inventory.models import BatchRecord
        
        query = select(BatchRecord).where(BatchRecord.item_id == item_id)
        if store_id:
            query = query.where(BatchRecord.store_id == store_id)
        
        query = query.order_by(BatchRecord.purchase_date.asc())
        
        result = await self.db.execute(query)
        batches = result.scalars().all()
        
        total_value = 0.0
        for batch in batches:
            quantity = batch.quantity or 0
            unit_cost = batch.purchase_price or 0
            total_value += quantity * unit_cost
        
        return total_value
    
    async def calculate_lifo_value(self, item_id: str, store_id: Optional[str] = None) -> float:
        """Calculate LIFO value for an item."""
        from app.core.inventory.models import BatchRecord
        
        query = select(BatchRecord).where(BatchRecord.item_id == item_id)
        if store_id:
            query = query.where(BatchRecord.store_id == store_id)
        
        query = query.order_by(BatchRecord.purchase_date.desc())
        
        result = await self.db.execute(query)
        batches = result.scalars().all()
        
        total_value = 0.0
        for batch in batches:
            quantity = batch.quantity or 0
            unit_cost = batch.purchase_price or 0
            total_value += quantity * unit_cost
        
        return total_value
