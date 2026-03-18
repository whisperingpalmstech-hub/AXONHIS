import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReactionType(StrEnum):
    ALLERGIC = "allergic"
    FEBRILE = "febrile"
    HEMOLYTIC = "hemolytic"
    ANAPHYLACTIC = "anaphylactic"


class ReactionSeverity(StrEnum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"


class TransfusionReaction(Base):
    __tablename__ = "transfusion_reactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    transfusion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transfusions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reaction_severity: Mapped[str] = mapped_column(String(50), nullable=False)
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_by: Mapped[str] = mapped_column(String(255), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    transfusion = relationship("Transfusion", primaryjoin="TransfusionReaction.transfusion_id == Transfusion.id")
