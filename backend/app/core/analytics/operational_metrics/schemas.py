from datetime import date
from pydantic import BaseModel, ConfigDict
import uuid

class OperationalMetricOut(BaseModel):
    id: uuid.UUID
    metric_date: date
    bed_occupancy_rate: float
    patient_throughput: int
    avg_task_completion_mins: float
    lab_processing_volume: int
    pharmacy_dispensing_volume: int
    staff_workload_index: float
    model_config = ConfigDict(from_attributes=True)
