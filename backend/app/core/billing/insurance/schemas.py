from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from typing import Optional
class InsuranceProviderBase(BaseModel):
    provider_name: str
    contact_details: Optional[str] = None
    policy_rules: Optional[str] = None
class InsuranceProviderCreate(InsuranceProviderBase): pass
class InsuranceProviderOut(InsuranceProviderBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class InsuranceClaimCreate(BaseModel):
    invoice_id: uuid.UUID
    provider_id: uuid.UUID
    claim_amount: float
class InsuranceClaimOut(InsuranceClaimCreate):
    id: uuid.UUID
    status: str
    submitted_at: datetime
    model_config = ConfigDict(from_attributes=True)
