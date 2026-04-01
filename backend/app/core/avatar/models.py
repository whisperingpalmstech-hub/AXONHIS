"""
AXONHIS Virtual Avatar – SQLAlchemy Models.

Tables:
  avatar_sessions       – conversation sessions
  avatar_messages       – individual messages in a session
  avatar_workflow_configs – admin-controlled workflow toggles & prompts
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class AvatarSession(Base):
    __tablename__ = "avatar_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    language = Column(String(10), default="en", nullable=False)
    status = Column(
        String(20), default="active", nullable=False
    )  # active | completed | abandoned
    patient_id = Column(UUID(as_uuid=True), nullable=True)  # linked after identification
    current_workflow = Column(String(50), nullable=True)
    workflow_step = Column(Integer, default=0)
    workflow_data = Column(Text, nullable=True)  # JSON blob for workflow state
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    messages = relationship("AvatarMessage", back_populates="session", cascade="all, delete-orphan")


class AvatarMessage(Base):
    __tablename__ = "avatar_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("avatar_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String(20), nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)
    workflow = Column(String(50), nullable=True)
    entities = Column(Text, nullable=True)  # JSON blob
    created_at = Column(DateTime, default=func.now(), nullable=False)

    session = relationship("AvatarSession", back_populates="messages")


class AvatarWorkflowConfig(Base):
    __tablename__ = "avatar_workflow_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_key = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    icon = Column(String(10), nullable=True)  # emoji
    system_prompt_override = Column(Text, nullable=True)
    supported_languages = Column(Text, nullable=True)  # JSON array
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
