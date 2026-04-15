"""Order Templates & Order Sets models – Phase 4."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderTemplate(Base):
    """Reusable order templates (e.g., 'Pneumonia workup')."""
    __tablename__ = "order_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_type: Mapped[str] = mapped_column(String(30), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    is_public: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    items: Mapped[list["OrderTemplateItem"]] = relationship(
        "OrderTemplateItem", back_populates="template", cascade="all, delete-orphan"
    )


class OrderTemplateItem(Base):
    """Items within an order template."""
    __tablename__ = "order_template_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("order_templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    item_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_quantity: Mapped[float] = mapped_column(default=1.0, nullable=False)
    default_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    template: Mapped["OrderTemplate"] = relationship("OrderTemplate", back_populates="items")


class OrderSet(Base):
    """Multi-domain order sets (e.g., 'ER Chest Pain Set')."""
    __tablename__ = "order_sets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    set_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_context: Mapped[str | None] = mapped_column(String(200), nullable=True)  # ER, ICU, General
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    is_public: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    items: Mapped[list["OrderSetItem"]] = relationship(
        "OrderSetItem", back_populates="order_set", cascade="all, delete-orphan"
    )


class OrderSetItem(Base):
    """Items within an order set (each linking to a specific order type)."""
    __tablename__ = "order_set_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("order_sets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_type: Mapped[str] = mapped_column(String(30), nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    item_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_quantity: Mapped[float] = mapped_column(default=1.0, nullable=False)
    default_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)

    order_set: Mapped["OrderSet"] = relationship("OrderSet", back_populates="items")
