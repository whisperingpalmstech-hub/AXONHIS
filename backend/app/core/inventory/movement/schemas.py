"""Stock Movement Analytics Schemas for Inventory."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class StockTransferCreate(BaseModel):
    """Schema for creating a stock transfer."""
    from_store_id: str
    to_store_id: str
    indent_id: Optional[str] = None
    notes: Optional[str] = None


class StockTransferItemCreate(BaseModel):
    """Schema for adding items to a transfer."""
    item_id: str
    batch_record_id: str
    requested_quantity: float


class StockTransferResponse(BaseModel):
    """Schema for stock transfer response."""
    id: str
    transfer_number: str
    from_store_id: str
    to_store_id: str
    indent_id: Optional[str] = None
    status: str
    requested_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    received_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TransferApprovalCreate(BaseModel):
    """Schema for transfer approval."""
    transfer_id: str
    approval_level: int
    comments: Optional[str] = None


class MovementReportRequest(BaseModel):
    """Schema for movement report request."""
    from_store_id: Optional[str] = None
    to_store_id: Optional[str] = None
    item_id: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    report_type: Optional[str] = None
