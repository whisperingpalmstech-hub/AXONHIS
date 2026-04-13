"""Stock Valuation Schemas for Inventory."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ValuationMethodCreate(BaseModel):
    """Schema for creating a valuation method."""
    method_name: str  # 'fifo', 'lifo', 'moving_average', 'weighted_average'
    description: Optional[str] = None
    is_default: bool = False
    is_active: bool = True


class StockValuationRequest(BaseModel):
    """Schema for stock valuation request."""
    store_id: Optional[str] = None
    valuation_method: str  # 'fifo', 'lifo', 'moving_average', 'weighted_average'


class StockAdjustmentCreate(BaseModel):
    """Schema for creating a stock adjustment."""
    item_id: str
    batch_record_id: str
    adjustment_type: str  # 'positive', 'negative'
    quantity: float
    reason: str
    adjustment_value: Optional[float] = None
