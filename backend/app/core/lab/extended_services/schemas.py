from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- Home Collection ---
class HomeCollectionCreate(BaseModel):
    patient_name: str
    patient_uhid: str
    address: str
    test_requested: str
    preferred_collection_time: datetime

class HomeCollectionOut(HomeCollectionCreate):
    id: str
    status: str
    test_order_id: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True

class PhlebotomistScheduleCreate(BaseModel):
    request_id: str
    collection_date: datetime
    collection_time: datetime
    assigned_phlebotomist: str
    collection_location: str

class PhlebotomistScheduleOut(PhlebotomistScheduleCreate):
    id: str
    status: str
    class Config: from_attributes = True

# --- Sample Transport ---
class SampleTransportCreate(BaseModel):
    sample_id: str
    test_order_id: str
    patient_uhid: str
    collection_time: datetime
    transport_personnel: str

class SampleTransportOut(SampleTransportCreate):
    id: str
    arrival_time_at_lab: Optional[datetime] = None
    status: str
    class Config: from_attributes = True

class TransportUpdate(BaseModel):
    status: str
    arrival_time_at_lab: Optional[datetime] = None

# --- Outsource Lab & Results ---
class OutsourceLabCreate(BaseModel):
    lab_name: str
    contact_details: str
    test_capabilities: str

class OutsourceLabOut(OutsourceLabCreate):
    id: str
    is_active: bool
    class Config: from_attributes = True

class ExternalResultCreate(BaseModel):
    outsource_lab_id: str
    test_order_id: str
    sample_id: str
    patient_uhid: str
    result_data: str

class ExternalResultOut(ExternalResultCreate):
    id: str
    imported_at: datetime
    is_validated: bool
    class Config: from_attributes = True

# --- Quality Control ---
class QualityControlCreate(BaseModel):
    test_name: str
    equipment_id: str
    result_value: float
    expected_value: float

class QualityControlOut(QualityControlCreate):
    id: str
    qc_date: datetime
    is_passed: bool
    failure_alert_sent: bool
    remarks: Optional[str] = None
    class Config: from_attributes = True

# --- Equipment Maintenance ---
class EquipmentMaintenanceCreate(BaseModel):
    equipment_id: str
    equipment_name: str
    maintenance_schedule: str
    last_calibration_date: datetime
    next_maintenance_date: datetime
    service_history: str

class EquipmentMaintenanceOut(EquipmentMaintenanceCreate):
    id: str
    is_overdue: bool
    class Config: from_attributes = True
