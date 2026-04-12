import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SurgicalTeam(Base):
    __tablename__ = "surgical_teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("surgery_schedule.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    lead_surgeon_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assistant_surgeon_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    anesthesiologist_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    scrub_nurse_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    circulating_nurse_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    schedule = relationship("SurgerySchedule", back_populates="team")
    lead_surgeon = relationship("User", foreign_keys=[lead_surgeon_id])
    assistant_surgeon = relationship("User", foreign_keys=[assistant_surgeon_id])
    anesthesiologist = relationship("User", foreign_keys=[anesthesiologist_id])
    scrub_nurse = relationship("User", foreign_keys=[scrub_nurse_id])
    circulating_nurse = relationship("User", foreign_keys=[circulating_nurse_id])

    def __repr__(self) -> str:
        return f"<SurgicalTeam schedule_id={self.schedule_id}>"
