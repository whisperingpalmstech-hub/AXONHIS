"""
AXONHIS CSSD (Central Sterile Services Department) Models.

Tracks surgical instrument sets, sterilization cycles (autoclave loads),
biological/chemical indicators, instrument traceability, and department workflows.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer, Text, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class SterilizationMethod(str, enum.Enum):
    steam_autoclave = "steam_autoclave"
    eto_gas = "eto_gas"
    plasma = "plasma"
    dry_heat = "dry_heat"
    chemical = "chemical"


class CycleStatus(str, enum.Enum):
    loading = "loading"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    released = "released"


class InstrumentCondition(str, enum.Enum):
    serviceable = "serviceable"
    damaged = "damaged"
    under_repair = "under_repair"
    condemned = "condemned"


# ─── Instrument Set Master ──────────────────────────────────
class InstrumentSet(Base):
    """A reusable set of surgical instruments (e.g., 'Major Abdominal Tray')"""
    __tablename__ = "cssd_instrument_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False, index=True)
    set_code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    department = Column(String(100), nullable=True)           # Owning department, e.g. 'General Surgery'
    instrument_count = Column(Integer, default=0)
    condition = Column(Enum(InstrumentCondition), default=InstrumentCondition.serviceable)
    is_active = Column(Boolean, default=True)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Sterilization Cycle ────────────────────────────────────
class SterilizationCycle(Base):
    """Tracks one autoclave/sterilizer load cycle"""
    __tablename__ = "cssd_sterilization_cycles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_number = Column(String(50), unique=True, nullable=False, index=True)
    machine_id = Column(String(50), nullable=False)            # Autoclave/sterilizer identifier
    method = Column(Enum(SterilizationMethod), nullable=False, default=SterilizationMethod.steam_autoclave)
    status = Column(Enum(CycleStatus), nullable=False, default=CycleStatus.loading)

    operator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    temperature_celsius = Column(Numeric(5, 1), nullable=True)
    pressure_psi = Column(Numeric(5, 1), nullable=True)
    exposure_minutes = Column(Integer, nullable=True)

    # Biological & Chemical Indicator Results
    bi_result = Column(String(20), nullable=True)             # 'pass' or 'fail'
    ci_result = Column(String(20), nullable=True)             # 'pass' or 'fail'

    notes = Column(Text, nullable=True)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Cycle-Set Link (many-to-many: which sets went in which cycle) ───
class CycleSetLink(Base):
    """Links instrument sets to a sterilization cycle"""
    __tablename__ = "cssd_cycle_set_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_id = Column(UUID(as_uuid=True), ForeignKey("cssd_sterilization_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    set_id = Column(UUID(as_uuid=True), ForeignKey("cssd_instrument_sets.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    cycle = relationship("SterilizationCycle")
    instrument_set = relationship("InstrumentSet")


# ─── CSSD Dispatch (issue sterile sets to OT/wards) ────────
class CSSDDispatch(Base):
    """Records issuance of sterile instrument sets to OT/wards"""
    __tablename__ = "cssd_dispatches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    set_id = Column(UUID(as_uuid=True), ForeignKey("cssd_instrument_sets.id", ondelete="CASCADE"), nullable=False)
    cycle_id = Column(UUID(as_uuid=True), ForeignKey("cssd_sterilization_cycles.id", ondelete="SET NULL"), nullable=True)
    destination_department = Column(String(100), nullable=False)  # e.g. 'OT-1', 'ER'
    dispatched_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    dispatched_at = Column(DateTime, default=datetime.utcnow)
    returned_at = Column(DateTime, nullable=True)
    return_condition = Column(Enum(InstrumentCondition), nullable=True)
    notes = Column(Text, nullable=True)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    instrument_set = relationship("InstrumentSet")
