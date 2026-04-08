from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Boolean, Integer, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class AdapterStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"
    DISCONNECTED = "DISCONNECTED"


class DeviceProtocol(str, enum.Enum):
    HL7 = "HL7"
    DICOM = "DICOM"
    FHIR = "FHIR"
    REST = "REST"
    MQTT = "MQTT"
    MODBUS = "MODBUS"
    TCP = "TCP"
    SERIAL = "SERIAL"
    CUSTOM = "CUSTOM"


class MdDeviceAdapter(Base):
    """
    Device Adapter model for integrating medical devices.
    Provides abstraction layer for device communication.
    """
    __tablename__ = "md_device_adapter"

    adapter_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    adapter_name = Column(String(255), nullable=False, unique=True)
    adapter_type = Column(String(50), nullable=False)  # ECG, BP_MONITOR, PULSE_OX, VENTILATOR, etc.
    protocol = Column(String(50), nullable=False)
    connection_config = Column(JSONB, nullable=False, default={})  # Connection parameters
    device_id = Column(UUID(as_uuid=True), ForeignKey("md_device.device_id"), nullable=True)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("md_facility.facility_id"), nullable=True)
    status = Column(String(30), default=AdapterStatus.INACTIVE, nullable=False, index=True)
    last_heartbeat = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    data_mapping = Column(JSONB, nullable=False, default={})  # Field mappings from device to system
    transformation_rules = Column(JSONB, nullable=False, default=[])  # Data transformation rules
    polling_interval_seconds = Column(Integer, default=30, nullable=False)
    auto_reconnect = Column(Boolean, default=True, nullable=False)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    device = relationship("MdDevice", backref="adapters")

    __table_args__ = (
        Index('idx_adapter_status', 'status'),
        Index('idx_adapter_type', 'adapter_type'),
    )


class MdDeviceData(Base):
    """
    Device data model for storing raw and processed device data.
    """
    __tablename__ = "md_device_data"

    data_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    adapter_id = Column(UUID(as_uuid=True), ForeignKey("md_device_adapter.adapter_id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=True, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("md_patient.patient_id", ondelete="CASCADE"), nullable=True, index=True)
    raw_data = Column(JSONB, nullable=False, default={})
    processed_data = Column(JSONB, nullable=False, default={})
    observation_type = Column(String(50), nullable=False, index=True)  # vital_sign, waveform, etc.
    data_quality_score = Column(Numeric(5,2), nullable=True)  # 0-100
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    status = Column(String(30), default="RECEIVED", nullable=False)  # RECEIVED, PROCESSED, ERROR

    # Relationships
    adapter = relationship("MdDeviceAdapter", backref="data_records")

    __table_args__ = (
        Index('idx_device_data_adapter_time', 'adapter_id', 'received_at'),
        Index('idx_device_data_patient_time', 'patient_id', 'received_at'),
    )


class MdAdapterCommand(Base):
    """
    Adapter command model for sending commands to devices.
    """
    __tablename__ = "md_adapter_command"

    command_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    adapter_id = Column(UUID(as_uuid=True), ForeignKey("md_device_adapter.adapter_id", ondelete="CASCADE"), nullable=False, index=True)
    command_type = Column(String(50), nullable=False)  # START, STOP, CALIBRATE, CONFIGURE, etc.
    command_payload = Column(JSONB, nullable=False, default={})
    status = Column(String(30), default="PENDING", nullable=False, index=True)  # PENDING, SENT, ACKNOWLEDGED, FAILED
    response_data = Column(JSONB, nullable=False, default={})
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    # Relationships
    adapter = relationship("MdDeviceAdapter", backref="commands")


class MdAdapterLog(Base):
    """
    Adapter log model for tracking adapter activity.
    """
    __tablename__ = "md_adapter_log"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    adapter_id = Column(UUID(as_uuid=True), ForeignKey("md_device_adapter.adapter_id", ondelete="CASCADE"), nullable=False, index=True)
    log_level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    meta_data = Column(JSONB, nullable=False, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    adapter = relationship("MdDeviceAdapter", backref="logs")

    __table_args__ = (
        Index('idx_adapter_log_adapter_time', 'adapter_id', 'created_at'),
    )
