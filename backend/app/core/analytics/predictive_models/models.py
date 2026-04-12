from sqlalchemy import Column, Date, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from app.database import Base

class HospitalPrediction(Base):
    __tablename__ = "analytics_predictive_models"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_date = Column(Date, nullable=False, index=True)
    prediction_type = Column(String(100), nullable=False, index=True) # e.g. "bed_demand", "lab_workload"
    predicted_value = Column(Float, nullable=False)
    confidence_interval_low = Column(Float, nullable=True)
    confidence_interval_high = Column(Float, nullable=True)
    factors = Column(JSONB, nullable=False, default=dict) # Features driving the prediction
