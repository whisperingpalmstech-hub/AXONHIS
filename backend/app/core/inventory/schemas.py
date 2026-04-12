from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import List, Optional

class StoreBase(BaseModel):
    name: str
    store_type: str
    parent_store_id: Optional[UUID4] = None

class StoreOut(StoreBase):
    id: UUID4
    is_active: bool
    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    item_code: str
    name: str
    category: str
    uom: str

class ItemOut(ItemBase):
    id: UUID4
    is_active: bool
    class Config:
        from_attributes = True

class OpeningBalance(BaseModel):
    store_id: UUID4
    item_id: UUID4
    batch_number: str
    expiry_date: datetime
    quantity: float
    purchase_price: float

class IndentItemCreate(BaseModel):
    item_id: UUID4
    requested_quantity: float

class IndentCreate(BaseModel):
    requesting_store_id: UUID4
    issuing_store_id: UUID4
    justification: Optional[str] = None
    items: List[IndentItemCreate]

class IssueItemCreate(BaseModel):
    item_id: UUID4
    batch_record_id: UUID4
    issued_quantity: float

class IssueCreate(BaseModel):
    indent_id: Optional[UUID4] = None
    issuing_store_id: UUID4
    receiving_store_id: UUID4
    items: List[IssueItemCreate]

    class Config:
        from_attributes = True
