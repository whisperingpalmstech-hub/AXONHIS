from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from typing import List
from app.core.billing.billing_entries.schemas import BillingEntryOut
class InvoiceCreate(BaseModel):
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
class InvoiceOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
    invoice_number: str
    total_amount: float
    status: str
    generated_at: datetime
    model_config = ConfigDict(from_attributes=True)
class InvoiceDetailOut(InvoiceOut):
    entries: List[BillingEntryOut] = []
