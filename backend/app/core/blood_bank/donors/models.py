import uuid
from datetime import date, datetime, timezone
from enum import StrEnum

from sqlalchemy import Integer, String, Date, Float, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScreeningStatus(StrEnum):
    ELIGIBLE = "eligible"
    TEMPORARILY_DEFERRED = "temporarily_deferred"
    PERMANENTLY_DEFERRED = "permanently_deferred"


class BloodDonor(Base):
    __tablename__ = "blood_donors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    donor_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    blood_group: Mapped[str] = mapped_column(String(10), nullable=False)
    rh_factor: Mapped[str] = mapped_column(String(10), nullable=False)
    contact_number: Mapped[str] = mapped_column(String(20), nullable=False)
    screening_status: Mapped[str] = mapped_column(String(50), nullable=False, default=ScreeningStatus.ELIGIBLE)
    last_donation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    collections: Mapped[list["BloodCollection"]] = relationship(
        "BloodCollection", back_populates="donor", cascade="all, delete-orphan"
    )


class BloodCollection(Base):
    __tablename__ = "blood_collections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    donor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("blood_donors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    collection_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    collection_location: Mapped[str] = mapped_column(String(255), nullable=False)
    collected_by: Mapped[str] = mapped_column(String(255), nullable=False)
    collection_volume: Mapped[float] = mapped_column(Float, nullable=False)  # ml
    screening_results: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    donor: Mapped["BloodDonor"] = relationship("BloodDonor", back_populates="collections")
