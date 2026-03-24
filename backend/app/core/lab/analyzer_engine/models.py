"""
LIS Analyzer & Device Integration Engine – Database Models

Tables:
  lis_analyzer_device       – registered analyzer devices
  lis_analyzer_worklist     – worklists sent to analyzers
  lis_analyzer_result       – results received from analyzers
  lis_reagent_usage         – reagent/consumable consumption tracking
  lis_device_error          – device error log
  lis_device_audit          – immutable device communication audit
"""
import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ── Enumerations ─────────────────────────────────────────────────────────────

class DeviceStatus(StrEnum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"
    ERROR = "ERROR"
    CALIBRATING = "CALIBRATING"


class DeviceProtocol(StrEnum):
    HL7 = "HL7"
    ASTM = "ASTM"
    SERIAL = "SERIAL"
    TCP_IP = "TCP_IP"
    USB = "USB"


class AnalyzerWorklistStatus(StrEnum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalyzerResultStatus(StrEnum):
    RECEIVED = "RECEIVED"
    MATCHED = "MATCHED"
    MISMATCH = "MISMATCH"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    IMPORTED = "IMPORTED"


class ErrorSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ── 1. Analyzer Device Registry ──────────────────────────────────────────────

class AnalyzerDevice(Base):
    """Registered laboratory analyzer devices."""
    __tablename__ = "lis_analyzer_device"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[str] = mapped_column(String(100), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    protocol: Mapped[str] = mapped_column(String(20), nullable=False, default=DeviceProtocol.HL7)
    connection_string: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=DeviceStatus.OFFLINE, index=True)
    last_communication: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_maintenance: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    test_code_mappings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_format_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ── 2. Analyzer Worklist ─────────────────────────────────────────────────────

class AnalyzerWorklist(Base):
    """Test worklists distributed to analyzers."""
    __tablename__ = "lis_analyzer_worklist"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_analyzer_device.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    sample_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    barcode: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    patient_uhid: Mapped[str | None] = mapped_column(String(50), nullable=True)
    patient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    test_code: Mapped[str] = mapped_column(String(50), nullable=False)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    analyzer_test_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="ROUTINE")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AnalyzerWorklistStatus.QUEUED, index=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── 3. Analyzer Results ──────────────────────────────────────────────────────

class AnalyzerResult(Base):
    """Results received from analyzer devices."""
    __tablename__ = "lis_analyzer_result"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_analyzer_device.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    worklist_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    sample_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    barcode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    test_code: Mapped[str] = mapped_column(String(50), nullable=False)
    analyzer_test_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    result_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    result_unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    result_flag: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AnalyzerResultStatus.RECEIVED, index=True
    )
    match_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_qc_sample: Mapped[bool] = mapped_column(default=False, nullable=False)
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ── 4. Reagent Usage Tracking ────────────────────────────────────────────────

class ReagentUsage(Base):
    """Reagent and consumable consumption per test run."""
    __tablename__ = "lis_reagent_usage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_analyzer_device.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    reagent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reagent_lot: Mapped[str | None] = mapped_column(String(100), nullable=True)
    test_code: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity_used: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="tests")
    current_stock: Mapped[float | None] = mapped_column(Float, nullable=True)
    reorder_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_low_stock: Mapped[bool] = mapped_column(default=False, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── 5. Device Error Log ──────────────────────────────────────────────────────

class DeviceError(Base):
    """Analyzer communication and processing errors."""
    __tablename__ = "lis_device_error"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lis_analyzer_device.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default=ErrorSeverity.ERROR)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(default=False, nullable=False)
    resolved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


# ── 6. Device Integration Audit ──────────────────────────────────────────────

class DeviceAudit(Base):
    """Immutable audit trail for all device communications."""
    __tablename__ = "lis_device_audit"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False, default="IN")
    data_transmitted: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_received: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="SUCCESS")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
