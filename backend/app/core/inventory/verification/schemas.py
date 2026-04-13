"""Physical Stock Verification Schemas for Inventory."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VerificationScheduleCreate(BaseModel):
    """Schema for creating a verification schedule."""
    store_id: Optional[str] = None
    verification_type: str  # 'full', 'partial', 'category_based'
    scheduled_date: datetime
    notes: Optional[str] = None


class VerificationItemCreate(BaseModel):
    """Schema for adding items to verification."""
    schedule_id: str
    item_id: str
    batch_record_id: str
    expected_quantity: float


class VerificationItemUpdate(BaseModel):
    """Schema for updating verification item."""
    verified_quantity: float
    variance_reason: Optional[str] = None


class DiscrepancyCreate(BaseModel):
    """Schema for creating a discrepancy."""
    verification_item_id: str
    discrepancy_type: str  # 'shortage', 'excess', 'damage'
    expected_quantity: float
    actual_quantity: float
    value: Optional[float] = None
    reason: Optional[str] = None
