from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
class BillingServiceBase(BaseModel):
    service_code: str
    service_name: str
    service_category: str
    department: str
class BillingServiceCreate(BillingServiceBase): pass
class BillingServiceOut(BillingServiceBase):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
