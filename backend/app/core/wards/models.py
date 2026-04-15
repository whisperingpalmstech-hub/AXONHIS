import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum, JSON, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Ward(Base):
    __tablename__ = "wards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), index=True, nullable=True) # Cross-tenant isolation
    ward_code = Column(String, unique=True, nullable=False)
    ward_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    floor = Column(String)
    capacity = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    rooms = relationship("Room", back_populates="ward", cascade="all, delete-orphan")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), index=True, nullable=True) # Cross-tenant isolation
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id", ondelete="CASCADE"), nullable=False)
    room_number = Column(String, nullable=False)
    room_type = Column(String(20), nullable=False) # private, semi_private, general
    capacity = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    ward = relationship("Ward", back_populates="rooms")
    beds = relationship("Bed", back_populates="room", cascade="all, delete-orphan")

class Bed(Base):
    __tablename__ = "beds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), index=True, nullable=True) # Cross-tenant isolation
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    bed_code = Column(String, unique=True, nullable=False)
    bed_number = Column(String, nullable=False)
    bed_type = Column(String(20), nullable=False) # standard, icu, isolation, pediatric
    status = Column(String(20), default="available", nullable=False) # available, occupied, cleaning, maintenance
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    room = relationship("Room", back_populates="beds")
    assignments = relationship("BedAssignment", back_populates="bed")
    cleaning_tasks = relationship("BedCleaningTask", back_populates="bed")

class BedAssignment(Base):
    __tablename__ = "bed_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), index=True, nullable=True) # Cross-tenant isolation
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False)
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), default="active", nullable=False) # active, transferred, discharged
    released_at = Column(DateTime(timezone=True), nullable=True)

    bed = relationship("Bed", back_populates="assignments")

class BedTransfer(Base):
    __tablename__ = "bed_transfers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), index=True, nullable=True) # Cross-tenant isolation
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="CASCADE"), nullable=False)
    from_bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id", ondelete="CASCADE"), nullable=False)
    to_bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id", ondelete="CASCADE"), nullable=False)
    transfer_reason = Column(String(255))
    transferred_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    transferred_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class BedCleaningTask(Base):
    __tablename__ = "bed_cleaning_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), index=True, nullable=True) # Cross-tenant isolation
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id", ondelete="CASCADE"), nullable=False)
    cleaning_status = Column(String(20), default="pending", nullable=False) # pending, in_progress, completed
    cleaning_started_at = Column(DateTime(timezone=True), nullable=True)
    cleaning_completed_at = Column(DateTime(timezone=True), nullable=True)
    cleaned_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    bed = relationship("Bed", back_populates="cleaning_tasks")
