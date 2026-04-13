"""Expiry Management Schemas for Inventory."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ExpiryAlertCreate(BaseModel):
    """Schema for creating an expiry alert."""
    alert_type: str  # 'warning', 'critical', 'expired'
    threshold_days: int
    is_active: bool = True


class ExpiryReportRequest(BaseModel):
    """Schema for generating expiry report."""
    report_type: str  # 'daily', 'weekly', 'monthly'
    store_id: Optional[str] = None


class ReturnToSupplierCreate(BaseModel):
    """Schema for creating a return to supplier request."""
    batch_record_id: str
    supplier_id: str
    return_quantity: float
    return_reason: str
    notes: Optional[str] = None


class DiscountSaleCreate(BaseModel):
    """Schema for creating a discount sale."""
    batch_record_id: str
    item_id: str
    original_price: float
    discount_percentage: float
    valid_from: datetime
    valid_to: datetime
