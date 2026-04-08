from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Boolean, Integer, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ConfigScope(str, enum.Enum):
    GLOBAL = "GLOBAL"
    FACILITY = "FACILITY"
    SPECIALTY = "SPECIALTY"
    USER = "USER"
    ENCOUNTER = "ENCOUNTER"


class ConfigDataType(str, enum.Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
    ARRAY = "ARRAY"


class MdConfigItem(Base):
    """
    Config-as-data model for externalized configuration.
    Allows configuration to be managed as data rather than code.
    """
    __tablename__ = "md_config_item"

    config_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_key = Column(String(255), nullable=False, index=True)
    config_value = Column(JSONB, nullable=False, default={})
    data_type = Column(String(20), nullable=False)  # STRING, NUMBER, BOOLEAN, JSON, ARRAY
    scope = Column(String(20), nullable=False, index=True)  # GLOBAL, FACILITY, SPECIALTY, USER, ENCOUNTER
    scope_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # ID of the scoped entity
    category = Column(String(100), nullable=False, index=True)  # AI, UI, WORKFLOW, INTEGRATION, etc.
    description = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, default=False, nullable=False)  # For encryption
    is_required = Column(Boolean, default=False, nullable=False)
    default_value = Column(JSONB, nullable=True)
    validation_rules = Column(JSONB, nullable=False, default={})  # Validation constraints
    version = Column(Integer, default=1, nullable=False)
    created_by = Column(String(100), nullable=False)
    updated_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    effective_from = Column(DateTime, nullable=True)
    effective_to = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_config_key_scope', 'config_key', 'scope'),
        Index('idx_config_category', 'category'),
        Index('idx_config_scope_id', 'scope', 'scope_id'),
    )


class MdConfigHistory(Base):
    """
    Config history model for tracking configuration changes.
    Provides audit trail for configuration changes.
    """
    __tablename__ = "md_config_history"

    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_id = Column(UUID(as_uuid=True), ForeignKey("md_config_item.config_id", ondelete="CASCADE"), nullable=False, index=True)
    config_key = Column(String(255), nullable=False)
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    change_reason = Column(Text, nullable=True)
    changed_by = Column(String(100), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    version = Column(Integer, nullable=False)

    # Relationships
    config = relationship("MdConfigItem", backref="history")

    __table_args__ = (
        Index('idx_config_history_config_time', 'config_id', 'changed_at'),
    )


class MdConfigGroup(Base):
    """
    Config group model for organizing related configuration items.
    """
    __tablename__ = "md_config_group"

    group_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_name = Column(String(255), unique=True, nullable=False)
    group_code = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    parent_group_id = Column(UUID(as_uuid=True), ForeignKey("md_config_group.group_id"), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Self-referential relationship
    parent = relationship("MdConfigGroup", remote_side=[group_id], backref="children")


class MdConfigGroupMapping(Base):
    """
    Config group mapping model.
    Maps configuration items to groups.
    """
    __tablename__ = "md_config_group_mapping"

    mapping_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("md_config_group.group_id", ondelete="CASCADE"), nullable=False)
    config_id = Column(UUID(as_uuid=True), ForeignKey("md_config_item.config_id", ondelete="CASCADE"), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    group = relationship("MdConfigGroup", backref="mappings")
    config = relationship("MdConfigItem", backref="group_mappings")

    __table_args__ = (
        Index('idx_config_group_mapping', 'group_id', 'config_id'),
    )
