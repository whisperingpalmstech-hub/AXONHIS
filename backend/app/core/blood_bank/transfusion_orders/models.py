import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TransfusionPriority(StrEnum):
    ROUTINE = "routine"
    URGENT = "urgent"
    STAT = "stat"


class AllocationStatus(StrEnum):
    RESERVED = "reserved"
    ISSUED = "issued"
    RETURNED = "returned"


class TransfusionOrder(Base):
    __tablename__ = "transfusion_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True, nullable=True) # Cross-tenant isolation
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # Reference to Phase 4 order
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("encounters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    requested_component_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("blood_components.id", ondelete="CASCADE"), nullable=False, index=True
    )
    units_requested: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    priority: Mapped[str] = mapped_column(String(50), default=TransfusionPriority.ROUTINE, nullable=False)
    order_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    allocations: Mapped[list["BloodAllocation"]] = relationship(
        "BloodAllocation", back_populates="transfusion_order", cascade="all, delete-orphan"
    )
    patient = relationship("Patient", primaryjoin="TransfusionOrder.patient_id == Patient.id")
    encounter = relationship("Encounter", primaryjoin="TransfusionOrder.encounter_id == Encounter.id")
    component = relationship("BloodComponent", primaryjoin="TransfusionOrder.requested_component_id == BloodComponent.id")


class BloodAllocation(Base):
    __tablename__ = "blood_allocations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True, nullable=True) # Cross-tenant isolation
    transfusion_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transfusion_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    blood_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("blood_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    allocated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    allocated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    allocation_status: Mapped[str] = mapped_column(String(50), default=AllocationStatus.RESERVED, nullable=False)

    transfusion_order: Mapped["TransfusionOrder"] = relationship(
        "TransfusionOrder", back_populates="allocations"
    )
    blood_unit = relationship("BloodUnit", primaryjoin="BloodAllocation.blood_unit_id == BloodUnit.id")
