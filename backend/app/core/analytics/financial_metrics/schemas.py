from datetime import date
from pydantic import BaseModel, ConfigDict
import uuid

class FinancialMetricOut(BaseModel):
    id: uuid.UUID
    metric_date: date
    daily_revenue: float
    outpatient_revenue: float
    inpatient_revenue: float
    insurance_claims_count: int
    claim_approval_rate: float
    billing_error_rate: float
    outstanding_invoices_amount: float
    model_config = ConfigDict(from_attributes=True)
