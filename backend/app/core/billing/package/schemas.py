"""Package Management Schemas for Billing Module."""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class PackageInclusionV2Base(BaseModel):
    """Base schema for package inclusion."""
    service_id: str
    service_name: str
    service_type: str
    quantity: int = 1
    is_mandatory: bool = False


class PackageInclusionV2Create(PackageInclusionV2Base):
    """Schema for creating a package inclusion."""
    pass


class PackageExclusionBase(BaseModel):
    """Base schema for package exclusion."""
    service_id: str
    service_name: str
    service_type: str
    exclusion_reason: Optional[str] = None


class PackageExclusionCreate(PackageExclusionBase):
    """Schema for creating a package exclusion."""
    pass


class PackagePricingBase(BaseModel):
    """Base schema for package pricing."""
    patient_category: str
    bed_type: Optional[str] = None
    payment_entitlement: Optional[str] = None
    price: float
    validity_start_date: Optional[datetime] = None
    validity_end_date: Optional[datetime] = None
    is_active: bool = True


class PackagePricingCreate(PackagePricingBase):
    """Schema for creating package pricing."""
    pass


class PackageApprovalRequest(BaseModel):
    """Schema for package approval request."""
    package_id: str
    request_type: str  # 'forceful_inclusion' or 'forceful_exclusion'
    service_id: str
    service_name: str
    reason: str


class PackageApprovalResponse(BaseModel):
    """Schema for package approval response."""
    id: str
    package_id: str
    request_type: str
    service_id: str
    service_name: str
    requested_by: str
    reason: str
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PackageCreate(BaseModel):
    """Schema for creating a package."""
    name: str
    description: Optional[str] = None
    package_type: str  # 'opd', 'ipd', 'daycare', 'gender_based'
    base_price: float
    inclusions: List[PackageInclusionV2Create]
    exclusions: List[PackageExclusionCreate] = []
    pricing: List[PackagePricingCreate]
    validity_start_date: Optional[datetime] = None
    validity_end_date: Optional[datetime] = None
    is_active: bool = True


class PackageUpdate(BaseModel):
    """Schema for updating a package (creates new version)."""
    name: Optional[str] = None
    description: Optional[str] = None
    version_name: Optional[str] = None
    changes_description: Optional[str] = None
    inclusions: Optional[List[PackageInclusionV2Create]] = None
    exclusions: Optional[List[PackageExclusionCreate]] = None
    pricing: Optional[List[PackagePricingCreate]] = None
    validity_start_date: Optional[datetime] = None
    validity_end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class PackageResponse(BaseModel):
    """Schema for package response."""
    id: str
    name: str
    description: Optional[str] = None
    package_type: str
    base_price: float
    validity_start_date: Optional[datetime] = None
    validity_end_date: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PackageWithDetailsResponse(PackageResponse):
    """Schema for package response with details."""
    inclusions: List[PackageInclusionV2Base]
    exclusions: List[PackageExclusionBase]
    pricing: List[PackagePricingBase]
    current_version: Optional[int] = None


class PackageProfitResponse(BaseModel):
    """Schema for package profit response."""
    id: str
    package_id: str
    patient_id: str
    package_cost: float
    package_price: float
    profit: float
    profit_percentage: float
    calculated_at: datetime

    class Config:
        from_attributes = True
