from sqlalchemy import Column, Date, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class DailyFinancialMetric(Base):
    __tablename__ = "analytics_financial_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_date = Column(Date, unique=True, nullable=False, index=True)
    daily_revenue = Column(Float, default=0.0, nullable=False)
    outpatient_revenue = Column(Float, default=0.0, nullable=False)
    inpatient_revenue = Column(Float, default=0.0, nullable=False)
    insurance_claims_count = Column(Integer, default=0, nullable=False)
    claim_approval_rate = Column(Float, default=0.0, nullable=False)
    billing_error_rate = Column(Float, default=0.0, nullable=False)
    outstanding_invoices_amount = Column(Float, default=0.0, nullable=False)
