from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
import uuid

class ModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class VendorMasterBase(BaseModel):
    vendor_code: str
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    rating: Optional[float] = 0.0

class VendorMasterCreate(VendorMasterBase): pass
class VendorMasterOut(VendorMasterBase, ModelOut):
    id: uuid.UUID
    is_active: bool

class PurchaseRequestItemBase(BaseModel):
    item_id: uuid.UUID
    requested_qty: float

class PurchaseRequestCreate(BaseModel):
    requesting_store_id: uuid.UUID
    delivery_store_id: uuid.UUID
    priority: str = "NORMAL"
    justification: Optional[str] = None
    items: List[PurchaseRequestItemBase]

class PurchaseRequestItemOut(PurchaseRequestItemBase, ModelOut):
    id: uuid.UUID
    approved_qty: Optional[float]
    ordered_qty: float

class PurchaseRequestOut(ModelOut):
    id: uuid.UUID
    pr_number: str
    requesting_store_id: uuid.UUID
    delivery_store_id: uuid.UUID
    priority: str
    justification: Optional[str]
    status: str
    created_at: datetime
    items: List[PurchaseRequestItemOut]

class PurchaseOrderItemBase(BaseModel):
    item_id: uuid.UUID
    ordered_qty: float
    rate: float
    tax_pct: float

class PurchaseOrderCreate(BaseModel):
    vendor_id: uuid.UUID
    pr_id: Optional[uuid.UUID] = None
    quotation_id: Optional[uuid.UUID] = None
    delivery_date: datetime
    warranty_terms: Optional[str] = None
    items: List[PurchaseOrderItemBase]

class PurchaseOrderItemOut(PurchaseOrderItemBase, ModelOut):
    id: uuid.UUID
    received_qty: float

class PurchaseOrderOut(ModelOut):
    id: uuid.UUID
    po_number: str
    vendor_id: uuid.UUID
    pr_id: Optional[uuid.UUID]
    quotation_id: Optional[uuid.UUID]
    total_amount: float
    tax_amount: float
    net_amount: float
    delivery_date: Optional[datetime]
    warranty_terms: Optional[str]
    status: str
    created_at: datetime
    items: List[PurchaseOrderItemOut]

class GRNItemCreate(BaseModel):
    po_item_id: uuid.UUID
    item_id: uuid.UUID
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    received_qty: float

class GRNCreate(BaseModel):
    po_id: uuid.UUID
    vendor_id: uuid.UUID
    store_id: uuid.UUID
    invoice_number: Optional[str] = None
    challan_number: Optional[str] = None
    items: List[GRNItemCreate]

class GRNItemOut(GRNItemCreate, ModelOut):
    id: uuid.UUID
    accepted_qty: float
    rejected_qty: float
    inspection_remarks: Optional[str]

class GRNOut(ModelOut):
    id: uuid.UUID
    grn_number: str
    po_id: uuid.UUID
    vendor_id: uuid.UUID
    store_id: uuid.UUID
    invoice_number: Optional[str]
    challan_number: Optional[str]
    status: str
    received_at: datetime
    items: List[GRNItemOut]

class GRNInspectionCommand(BaseModel):
    accepted_qty: float
    rejected_qty: float
    inspection_remarks: Optional[str] = None
