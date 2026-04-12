from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from typing import Optional
class ServiceTariffCreate(BaseModel):
    service_id: uuid.UUID
    price: float
    currency: str = "USD"
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
class ServiceTariffOut(ServiceTariffCreate):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)
