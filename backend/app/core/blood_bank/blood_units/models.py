import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import Integer, String, Date, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BloodUnitStatus(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    ISSUED = "issued"
    EXPIRED = "expired"
    DISCARDED = "discarded"


class BloodUnit(Base):
    __tablename__ = "blood_units"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    unit_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    blood_group: Mapped[str] = mapped_column(String(10), nullable=False)
    rh_factor: Mapped[str] = mapped_column(String(10), nullable=False)
    component_type: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("blood_components.id", ondelete="SET NULL"), nullable=True, index=True
    )
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("blood_collections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    collection_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    storage_location: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("blood_storage_units.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default=BloodUnitStatus.AVAILABLE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    component: Mapped["BloodComponent"] = relationship(
        "BloodComponent",
        primaryjoin="BloodUnit.component_type == BloodComponent.id",
    )
    collection: Mapped["BloodCollection"] = relationship(
        "BloodCollection",
        primaryjoin="BloodUnit.collection_id == BloodCollection.id",
    )
    storage: Mapped["BloodStorageUnit"] = relationship(
        "BloodStorageUnit",
        primaryjoin="BloodUnit.storage_location == BloodStorageUnit.id",
    )

    # I'll rely on string-based references in relationship definition to avoid circular imports.
