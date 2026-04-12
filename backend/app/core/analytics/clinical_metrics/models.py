from sqlalchemy import Column, Date, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class DailyClinicalMetric(Base):
    __tablename__ = "analytics_clinical_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_date = Column(Date, unique=True, nullable=False, index=True)
    admissions_count = Column(Integer, default=0, nullable=False)
    readmission_rate = Column(Float, default=0.0, nullable=False)
    average_los_hours = Column(Float, default=0.0, nullable=False)
    avg_lab_turnaround_hours = Column(Float, default=0.0, nullable=False)
    critical_alerts_count = Column(Integer, default=0, nullable=False)
    avg_alert_response_mins = Column(Float, default=0.0, nullable=False)
