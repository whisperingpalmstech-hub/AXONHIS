from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

# Batch Schemas
class BatchCreate(BaseModel):
    drug_id: UUID
    store_id: str
    batch_number: str
    expiry_date: date
    available_quantity: Decimal
    purchase_price: Decimal
    selling_price: Decimal

class BatchOut(BaseModel):
    id: UUID
    drug_id: UUID
    store_id: str
    batch_number: str
    expiry_date: date
    available_quantity: Decimal
    purchase_price: Decimal
    selling_price: Decimal

    model_config = ConfigDict(from_attributes=True)

# Item Kit Schemas
class KitComponent(BaseModel):
    drug_id: str
    quantity: Decimal

class KitCreate(BaseModel):
    kit_name: str
    description: Optional[str] = None
    kit_components: List[KitComponent]

class KitOut(KitCreate):
    id: UUID
    status: str

    model_config = ConfigDict(from_attributes=True)

# Analysis Schemas
class AnalysisUpdate(BaseModel):
    abc_category: Optional[str] = None
    ved_category: Optional[str] = None
    is_dead_stock: Optional[int] = None

class AnalysisOut(BaseModel):
    id: UUID
    drug_id: UUID
    abc_category: Optional[str]
    ved_category: Optional[str]
    is_dead_stock: int
    last_analyzed: datetime

    model_config = ConfigDict(from_attributes=True)

# Alerts Out
class AlertOut(BaseModel):
    id: UUID
    alert_type: str
    drug_id: Optional[UUID]
    batch_id: Optional[UUID]
    store_id: str
    message: str
    alert_date: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)
