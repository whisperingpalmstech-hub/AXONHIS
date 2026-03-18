from pydantic import BaseModel, ConfigDict, Field
import uuid
from datetime import datetime
from typing import Optional, List, Any

# --- Provider ---
class InsuranceProviderBase(BaseModel):
    provider_name: str
    provider_code: Optional[str] = None
    contact_details: Optional[str] = None
    billing_address: Optional[str] = None
    is_active: bool = True

class InsuranceProviderCreate(InsuranceProviderBase): pass
class InsuranceProviderOut(InsuranceProviderBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# --- Package ---
class InsurancePackageBase(BaseModel):
    provider_id: uuid.UUID
    package_name: str
    default_co_pay_percent: float = 0
    default_deductible: float = 0
    annual_limit: Optional[float] = None
    coverage_details: Optional[Any] = None # JSON

class InsurancePackageCreate(InsurancePackageBase): pass
class InsurancePackageOut(InsurancePackageBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

# --- Policy ---
class InsurancePolicyBase(BaseModel):
    patient_id: uuid.UUID
    package_id: uuid.UUID
    policy_number: str
    priority: int = 1
    group_number: Optional[str] = None
    status: str = "active"
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None

class InsurancePolicyCreate(InsurancePolicyBase): pass
class InsurancePolicyOut(InsurancePolicyBase):
    id: uuid.UUID
    package: Optional[InsurancePackageOut] = None
    model_config = ConfigDict(from_attributes=True)

# --- Pre-Auth ---
class PreAuthorizationBase(BaseModel):
    patient_id: uuid.UUID
    provider_id: uuid.UUID
    service_id: uuid.UUID
    request_amount: float
    clinical_notes: Optional[str] = None

class PreAuthorizationCreate(PreAuthorizationBase): pass
class PreAuthorizationUpdate(BaseModel):
    auth_code: Optional[str] = None
    approved_amount: Optional[float] = None
    status: Optional[str] = None
    validity_date: Optional[datetime] = None

class PreAuthorizationOut(PreAuthorizationBase):
    id: uuid.UUID
    auth_code: Optional[str] = None
    approved_amount: float
    status: str
    request_date: datetime
    validity_date: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# --- Claim ---
class ClaimItemBase(BaseModel):
    billing_entry_id: uuid.UUID
    amount: float
    status: str = "pended"
    remark: Optional[str] = None

class ClaimItemCreate(ClaimItemBase): pass
class ClaimItemOut(ClaimItemBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class InsuranceClaimBase(BaseModel):
    invoice_id: uuid.UUID
    provider_id: uuid.UUID
    claim_number: Optional[str] = None
    claim_amount: float

class InsuranceClaimCreate(InsuranceClaimBase):
    items: List[ClaimItemCreate] = []

class InsuranceClaimUpdate(BaseModel):
    allowed_amount: Optional[float] = None
    paid_amount: Optional[float] = None
    rejection_reason: Optional[str] = None
    status: Optional[str] = None

class InsuranceClaimOut(InsuranceClaimBase):
    id: uuid.UUID
    claim_number: Optional[str] = None
    allowed_amount: float
    paid_amount: float
    rejection_reason: Optional[str] = None
    status: str
    submitted_at: datetime
    last_updated: Optional[datetime] = None
    items: List[ClaimItemOut] = []
    model_config = ConfigDict(from_attributes=True)
