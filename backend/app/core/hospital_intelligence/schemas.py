from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime

class AnalyticsBaseStatsOut(BaseModel):
    total_patients_registered_today: int
    total_opd_visits_today: int
    patients_waiting: int
    avg_waiting_time_mins: float
    patients_in_consultation: int

class AnalyticsDoctorProductivityOut(BaseModel):
    doctor_name: str
    department: str
    patients_seen: int
    avg_consult_time_mins: float
    revenue_generated: float
    
class AnalyticsRevenueSplitOut(BaseModel):
    department: str
    net_revenue: float
    
class AnalyticsClinicalDiseaseOut(BaseModel):
    disease_name: str
    incidence_count: int
    
class AnalyticsCrowdPredictionOut(BaseModel):
    target_date: date
    department: str
    predicted_footfall: int
    peak_hours_expected: str
    is_anomaly_alert: bool

class ManagementIntelligenceDashboardOut(BaseModel):
    referral_sources: Dict[str, float]
    retention_rate_pct: float
    
class ExportFormatRequest(BaseModel):
    report_type: str
    format: str # PDF, Excel, CSV
    date_range_start: date
    date_range_end: date
    department: Optional[str] = None
