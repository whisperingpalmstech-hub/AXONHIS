import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    Date,
    JSON,
    Boolean,
    ForeignKey,
    Numeric
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.database import Base

# ── Data Warehouse: Analytics Patient Flow ────────────────────
class AnalyticsPatientFlow(Base):
    __tablename__ = "analytics_patient_flow"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_date = Column(Date, index=True, default=date.today)
    department = Column(String, index=True)
    total_registered = Column(Integer, default=0)
    total_consulted = Column(Integer, default=0)
    total_no_shows = Column(Integer, default=0)
    avg_waiting_time_mins = Column(Float, default=0.0)
    avg_consult_duration_mins = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ── Data Warehouse: Analytics Doctor Productivity ──────────────
class AnalyticsDoctorProductivity(Base):
    __tablename__ = "analytics_doctor_productivity"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_date = Column(Date, index=True, default=date.today)
    doctor_name = Column(String, index=True)
    department = Column(String, index=True)
    patients_seen = Column(Integer, default=0)
    avg_consult_time_mins = Column(Float, default=0.0)
    revenue_generated = Column(Numeric(10, 2), default=0.0)
    orders_prescribed = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ── Data Warehouse: Analytics Revenue ──────────────────────────
class AnalyticsRevenue(Base):
    __tablename__ = "analytics_revenue"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_date = Column(Date, index=True, default=date.today)
    department = Column(String, index=True)
    gross_revenue = Column(Numeric(12, 2), default=0.0)
    discounts_given = Column(Numeric(10, 2), default=0.0)
    net_revenue = Column(Numeric(12, 2), default=0.0)
    payment_modes_split = Column(JSON, default=dict) # e.g. {"card": 500, "cash": 200}
    payer_type_split = Column(JSON, default=dict) # e.g. {"insurance": 50, "corporate": 10, "self_pay": 40}
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ── Data Warehouse: Analytics Clinical Stats ────────────────────
class AnalyticsClinicalStatistics(Base):
    __tablename__ = "analytics_clinical_statistics"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_date = Column(Date, index=True, default=date.today)
    disease_icd_code = Column(String, index=True)
    disease_name = Column(String)
    incidence_count = Column(Integer, default=0)
    prescriptions_generated = Column(Integer, default=0)
    follow_up_compliance_rate_pct = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ── Data Warehouse: Predictive Models ──────────────────────────
class AnalyticsCrowdPrediction(Base):
    __tablename__ = "analytics_prediction_models"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_date = Column(Date, index=True)
    department = Column(String, index=True)
    predicted_footfall = Column(Integer, default=0)
    confidence_score_pct = Column(Float, default=0.0)
    peak_hours_expected = Column(String) # e.g. '10:00 AM - 1:30 PM'
    is_anomaly_alert = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
