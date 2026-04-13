"""Taxation Module Schemas for Billing."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaxCreate(BaseModel):
    """Schema for creating a tax."""
    tax_code: str
    tax_name: str
    tax_type: str  # 'gst', 'service_tax', 'vat', 'cess', 'surcharge'
    tax_percentage: float
    description: Optional[str] = None
    is_active: bool = True
    effective_from: datetime
    effective_to: Optional[datetime] = None


class TaxUpdate(BaseModel):
    """Schema for updating a tax."""
    tax_name: Optional[str] = None
    tax_percentage: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    effective_to: Optional[datetime] = None


class TaxApplicabilityCreate(BaseModel):
    """Schema for creating tax applicability."""
    tax_id: str
    service_id: str
    service_name: str
    service_type: str  # 'hospital_service', 'lab', 'radiology', 'pharmacy'
    patient_category: Optional[str] = None  # 'national', 'foreign', 'bpl'
    is_applicable: bool = True
    validity_start_date: Optional[datetime] = None
    validity_end_date: Optional[datetime] = None


class TaxValidityCreate(BaseModel):
    """Schema for creating tax validity period."""
    tax_id: str
    valid_from: datetime
    valid_to: Optional[datetime] = None
    tax_percentage: float
    reason: Optional[str] = None
