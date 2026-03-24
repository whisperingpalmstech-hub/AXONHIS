from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Float, Text, Enum
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class LisHomeCollectionRequest(Base):
    __tablename__ = "lis_home_collection_requests"
    id = Column(String, primary_key=True, default=gen_uuid)
    patient_name = Column(String, index=True)
    patient_uhid = Column(String, index=True)
    address = Column(Text)
    test_requested = Column(String)
    preferred_collection_time = Column(DateTime)
    status = Column(String, default="Pending") # Pending, Scheduled, Collected, Cancelled
    test_order_id = Column(String, index=True, nullable=True) # Linked to core LIS
    created_at = Column(DateTime, default=datetime.utcnow)

class LisPhlebotomistSchedule(Base):
    __tablename__ = "lis_phlebotomist_schedule"
    id = Column(String, primary_key=True, default=gen_uuid)
    request_id = Column(String, ForeignKey("lis_home_collection_requests.id"))
    collection_date = Column(DateTime)
    collection_time = Column(DateTime)
    assigned_phlebotomist = Column(String, index=True)
    collection_location = Column(Text)
    status = Column(String, default="Scheduled") # Scheduled, Arrived, Collected
    
    request = relationship("LisHomeCollectionRequest", backref="schedules")

# NOTE: Sample Transport is managed by the Phlebotomy Engine
# (app.core.lab.phlebotomy_engine.models.SampleTransport)
# No duplicate table needed here — Extended Services references it directly.

class LisOutsourceLabMaster(Base):
    __tablename__ = "lis_outsource_lab_master"
    id = Column(String, primary_key=True, default=gen_uuid)
    lab_name = Column(String, index=True)
    contact_details = Column(String)
    test_capabilities = Column(Text) # JSON or comma separated string
    is_active = Column(Boolean, default=True)

class LisExternalResult(Base):
    __tablename__ = "lis_external_results"
    id = Column(String, primary_key=True, default=gen_uuid)
    outsource_lab_id = Column(String, ForeignKey("lis_outsource_lab_master.id"))
    test_order_id = Column(String, index=True)
    sample_id = Column(String, index=True)
    patient_uhid = Column(String, index=True)
    result_data = Column(Text) # The imported report text or structured JSON
    imported_at = Column(DateTime, default=datetime.utcnow)
    is_validated = Column(Boolean, default=False)
    
    lab = relationship("LisOutsourceLabMaster")

class LisQualityControl(Base):
    __tablename__ = "lis_quality_control"
    id = Column(String, primary_key=True, default=gen_uuid)
    test_name = Column(String, index=True)
    equipment_id = Column(String, index=True)
    qc_date = Column(DateTime, default=datetime.utcnow)
    result_value = Column(Float)
    expected_value = Column(Float)
    is_passed = Column(Boolean)
    failure_alert_sent = Column(Boolean, default=False)
    remarks = Column(String, nullable=True)

class LisEquipmentMaintenance(Base):
    __tablename__ = "lis_equipment_maintenance"
    id = Column(String, primary_key=True, default=gen_uuid)
    equipment_id = Column(String, index=True)
    equipment_name = Column(String)
    maintenance_schedule = Column(String) # e.g. "Weekly", "Montly"
    last_calibration_date = Column(DateTime)
    next_maintenance_date = Column(DateTime)
    service_history = Column(Text) # Log of services
    is_overdue = Column(Boolean, default=False)
