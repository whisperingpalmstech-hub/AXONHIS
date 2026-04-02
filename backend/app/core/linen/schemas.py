from pydantic import BaseModel, UUID4, Field
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal

class LinenCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    expected_lifespan_washes: int = 100
    is_active: bool = True

class LinenCategoryCreate(LinenCategoryBase):
    pass

class LinenCategoryOut(LinenCategoryBase):
    id: UUID4
    org_id: Optional[UUID4]
    created_at: datetime

    class Config:
        from_attributes = True

class LinenInventoryLedgerBase(BaseModel):
    category_id: UUID4
    department_id: str
    clean_quantity: int = 0
    dirty_quantity: int = 0
    in_wash_quantity: int = 0

class LinenInventoryLedgerOut(LinenInventoryLedgerBase):
    id: UUID4
    org_id: Optional[UUID4]
    last_updated: datetime

    category: LinenCategoryOut

    class Config:
        from_attributes = True

class LaundryBatchCreate(BaseModel):
    batch_number: str
    washer_machine_id: Optional[str] = None
    total_weight_kg: Optional[Decimal] = None
    notes: Optional[str] = None

class LaundryBatchStatusUpdate(BaseModel):
    status: str
    end_time: Optional[datetime] = None

class LaundryBatchOut(LaundryBatchCreate):
    id: UUID4
    operator_id: Optional[UUID4]
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    org_id: Optional[UUID4]

    class Config:
        from_attributes = True

class LinenTransactionCreate(BaseModel):
    transaction_type: str
    category_id: UUID4
    quantity: int
    source_department: Optional[str] = None
    destination_department: Optional[str] = None
    batch_id: Optional[UUID4] = None
    notes: Optional[str] = None

class LinenTransactionOut(BaseModel):
    id: UUID4
    transaction_type: str
    category_id: UUID4
    quantity: int
    source_department: Optional[str]
    destination_department: Optional[str]
    batch_id: Optional[UUID4]
    performed_by: UUID4
    transaction_date: datetime
    notes: Optional[str]
    org_id: Optional[UUID4]

    category: LinenCategoryOut

    class Config:
        from_attributes = True
