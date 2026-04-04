import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class VendorMaster(Base):
    __tablename__ = "proc_vendor_master"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_code = Column(String(50), unique=True, index=True)
    name = Column(String(200), nullable=False)
    contact_person = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    tax_id = Column(String(50)) # GSTIN etc
    payment_terms = Column(String(100))
    rating = Column(Numeric(3, 2), default=0.0)
    is_active = Column(Boolean, default=True)

class PurchaseRequest(Base):
    __tablename__ = "proc_purchase_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pr_number = Column(String(50), unique=True, index=True)
    requesting_store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id"), nullable=False)
    delivery_store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id"), nullable=False)
    priority = Column(String(20), default="NORMAL") # NORMAL, URGENT
    justification = Column(Text)
    status = Column(String(50), default="PENDING_APPROVAL") # PENDING_APPROVAL, APPROVED, REJECTED, PO_GENERATED, PARTIAL_PO
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    items = relationship("PurchaseRequestItem", backref="purchase_request")

class PurchaseRequestItem(Base):
    __tablename__ = "proc_pr_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pr_id = Column(UUID(as_uuid=True), ForeignKey("proc_purchase_requests.id", ondelete="CASCADE"))
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id"))
    requested_qty = Column(Numeric(12, 2), nullable=False)
    approved_qty = Column(Numeric(12, 2))
    ordered_qty = Column(Numeric(12, 2), default=0.0)

class VendorQuotation(Base):
    __tablename__ = "proc_vendor_quotations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_number = Column(String(50), unique=True)
    pr_id = Column(UUID(as_uuid=True), ForeignKey("proc_purchase_requests.id"))
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("proc_vendor_master.id"))
    total_amount = Column(Numeric(14, 2))
    status = Column(String(50), default="RECEIVED") # RECEIVED, ACCEPTED, REJECTED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class QuotationItem(Base):
    __tablename__ = "proc_quotation_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("proc_vendor_quotations.id", ondelete="CASCADE"))
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id"))
    quoted_qty = Column(Numeric(12, 2))
    quoted_rate = Column(Numeric(12, 2))
    discount_pct = Column(Numeric(5, 2), default=0.0)
    tax_pct = Column(Numeric(5, 2), default=0.0)

class PurchaseOrder(Base):
    __tablename__ = "proc_purchase_orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(50), unique=True, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("proc_vendor_master.id"))
    pr_id = Column(UUID(as_uuid=True), ForeignKey("proc_purchase_requests.id"), nullable=True)
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("proc_vendor_quotations.id"), nullable=True)
    total_amount = Column(Numeric(14, 2))
    tax_amount = Column(Numeric(14, 2))
    net_amount = Column(Numeric(14, 2))
    delivery_date = Column(DateTime(timezone=True))
    warranty_terms = Column(Text)
    status = Column(String(50), default="DRAFT") # DRAFT, PENDING_APPROVAL, SENT, PARTIAL_GRN, FULL_GRN, CLOSED
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    items = relationship("PurchaseOrderItem", backref="purchase_order")

class PurchaseOrderItem(Base):
    __tablename__ = "proc_po_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_id = Column(UUID(as_uuid=True), ForeignKey("proc_purchase_orders.id", ondelete="CASCADE"))
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id"))
    ordered_qty = Column(Numeric(12, 2))
    rate = Column(Numeric(12, 2))
    tax_pct = Column(Numeric(5, 2), default=0.0)
    received_qty = Column(Numeric(12, 2), default=0.0)

class GoodsReceiptNote(Base):
    __tablename__ = "proc_grn"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grn_number = Column(String(50), unique=True, index=True)
    po_id = Column(UUID(as_uuid=True), ForeignKey("proc_purchase_orders.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("proc_vendor_master.id"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("inv_stores.id"), nullable=False)
    invoice_number = Column(String(100))
    challan_number = Column(String(100))
    status = Column(String(50), default="INSPECTION_PENDING") # INSPECTION_PENDING, APPROVED, REJECTED, SETTLED
    received_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    items = relationship("GRNItem", backref="grn")

class GRNItem(Base):
    __tablename__ = "proc_grn_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grn_id = Column(UUID(as_uuid=True), ForeignKey("proc_grn.id", ondelete="CASCADE"))
    po_item_id = Column(UUID(as_uuid=True), ForeignKey("proc_po_items.id"))
    item_id = Column(UUID(as_uuid=True), ForeignKey("inv_items.id"))
    batch_number = Column(String(100))
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    received_qty = Column(Numeric(12, 2))
    accepted_qty = Column(Numeric(12, 2), default=0.0)
    rejected_qty = Column(Numeric(12, 2), default=0.0)
    inspection_remarks = Column(Text)

class ReturnGatepass(Base):
    __tablename__ = "proc_return_gatepass"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rgp_number = Column(String(50), unique=True)
    grn_id = Column(UUID(as_uuid=True), ForeignKey("proc_grn.id"))
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("proc_vendor_master.id"))
    reason = Column(Text)
    status = Column(String(50), default="PENDING") # PENDING, DISPATCHED, RETURNED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ProcurmentSettlement(Base):
    __tablename__ = "proc_vendor_settlements"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    settlement_number = Column(String(50), unique=True)
    grn_id = Column(UUID(as_uuid=True), ForeignKey("proc_grn.id"))
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("proc_vendor_master.id"))
    payment_method = Column(String(50)) # CASH, CHEQUE, BANK_TRANSFER
    amount_paid = Column(Numeric(14, 2))
    transaction_ref = Column(String(100))
    status = Column(String(50), default="COMPLETED")
    settled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
