from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
class PaymentCreate(BaseModel):
    invoice_id: uuid.UUID
    payment_method: str
    amount: float
class PaymentOut(PaymentCreate):
    id: uuid.UUID
    payment_status: str
    payment_time: datetime
    model_config = ConfigDict(from_attributes=True)
