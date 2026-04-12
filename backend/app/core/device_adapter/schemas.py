from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class AdapterStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"
    DISCONNECTED = "DISCONNECTED"


class DeviceProtocol(str, Enum):
    HL7 = "HL7"
    DICOM = "DICOM"
    FHIR = "FHIR"
    REST = "REST"
    MQTT = "MQTT"
    MODBUS = "MODBUS"
    TCP = "TCP"
    SERIAL = "SERIAL"
    CUSTOM = "CUSTOM"


class DeviceAdapterCreate(BaseModel):
    adapter_name: str
    adapter_type: str
    protocol: DeviceProtocol
    connection_config: dict = Field(default_factory=dict)
    device_id: Optional[UUID] = None
    facility_id: Optional[UUID] = None
    data_mapping: dict = Field(default_factory=dict)
    transformation_rules: List[dict] = Field(default_factory=list)
    polling_interval_seconds: int = Field(default=30, ge=1)
    auto_reconnect: bool = True
    created_by: str


class DeviceAdapterUpdate(BaseModel):
    adapter_name: Optional[str] = None
    connection_config: Optional[dict] = None
    data_mapping: Optional[dict] = None
    transformation_rules: Optional[List[dict]] = None
    polling_interval_seconds: Optional[int] = Field(None, ge=1)
    auto_reconnect: Optional[bool] = None
    status: Optional[AdapterStatus] = None


class DeviceAdapterResponse(BaseModel):
    adapter_id: UUID
    adapter_name: str
    adapter_type: str
    protocol: str
    connection_config: dict
    device_id: Optional[UUID]
    facility_id: Optional[UUID]
    status: AdapterStatus
    last_heartbeat: Optional[datetime]
    last_error: Optional[str]
    data_mapping: dict
    transformation_rules: List[dict]
    polling_interval_seconds: int
    auto_reconnect: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceDataCreate(BaseModel):
    adapter_id: UUID
    encounter_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    raw_data: dict = Field(default_factory=dict)
    observation_type: str


class DeviceDataResponse(BaseModel):
    data_id: UUID
    adapter_id: UUID
    encounter_id: Optional[UUID]
    patient_id: Optional[UUID]
    raw_data: dict
    processed_data: dict
    observation_type: str
    data_quality_score: Optional[float]
    received_at: datetime
    processed_at: Optional[datetime]
    status: str

    class Config:
        from_attributes = True


class AdapterCommandCreate(BaseModel):
    adapter_id: UUID
    command_type: str
    command_payload: dict = Field(default_factory=dict)


class AdapterCommandResponse(BaseModel):
    command_id: UUID
    adapter_id: UUID
    command_type: str
    command_payload: dict
    status: str
    response_data: dict
    error_message: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]
    acknowledged_at: Optional[datetime]

    class Config:
        from_attributes = True


class AdapterHealthCheck(BaseModel):
    adapter_id: UUID
    adapter_name: str
    status: AdapterStatus
    last_heartbeat: Optional[datetime]
    is_connected: bool
    data_points_last_hour: int
    error_count_last_hour: int
