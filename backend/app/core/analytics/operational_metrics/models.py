from sqlalchemy import Column, Date, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class DailyOperationalMetric(Base):
    __tablename__ = "analytics_operational_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_date = Column(Date, unique=True, nullable=False, index=True)
    bed_occupancy_rate = Column(Float, default=0.0, nullable=False)
    patient_throughput = Column(Integer, default=0, nullable=False)
    avg_task_completion_mins = Column(Float, default=0.0, nullable=False)
    lab_processing_volume = Column(Integer, default=0, nullable=False)
    pharmacy_dispensing_volume = Column(Integer, default=0, nullable=False)
    staff_workload_index = Column(Float, default=0.0, nullable=False)
