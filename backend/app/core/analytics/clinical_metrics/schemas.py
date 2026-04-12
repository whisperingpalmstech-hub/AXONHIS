from datetime import date
from pydantic import BaseModel, ConfigDict
import uuid

class ClinicalMetricOut(BaseModel):
    id: uuid.UUID
    metric_date: date
    admissions_count: int
    readmission_rate: float
    average_los_hours: float
    avg_lab_turnaround_hours: float
    critical_alerts_count: int
    avg_alert_response_mins: float
    model_config = ConfigDict(from_attributes=True)
