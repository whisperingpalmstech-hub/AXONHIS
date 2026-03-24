import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, JSON, Text, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class RpiwUserRole(Base):
    """Maps users to their clinical roles and departments."""
    __tablename__ = "rpiw_user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_code = Column(String, nullable=False, index=True)  # doctor, nurse, phlebotomist, pharmacist, admin
    role_label = Column(String, nullable=False)  # Display name
    department = Column(String, nullable=True)
    is_primary = Column(Boolean, default=True)  # A user can have multiple roles; one is primary
    is_active = Column(Boolean, default=True)
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    assigned_by = Column(String, nullable=True)


class RpiwRolePermission(Base):
    """Defines granular permissions for each role."""
    __tablename__ = "rpiw_role_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_code = Column(String, nullable=False, index=True)
    permission_key = Column(String, nullable=False)  # e.g. orders.create, vitals.record, samples.collect
    permission_label = Column(String, nullable=False)
    resource_type = Column(String, nullable=True)  # orders, vitals, samples, notes, medications
    can_create = Column(Boolean, default=False)
    can_read = Column(Boolean, default=True)
    can_update = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)


class RpiwRoleWorkflow(Base):
    """Maps workflows to specific roles."""
    __tablename__ = "rpiw_role_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_code = Column(String, nullable=False, index=True)
    workflow_key = Column(String, nullable=False)  # e.g. review_patient_summary, record_vitals
    workflow_label = Column(String, nullable=False)
    workflow_description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    icon = Column(String, nullable=True)  # Icon identifier for frontend
    route_path = Column(String, nullable=True)  # Frontend route
    is_active = Column(Boolean, default=True)


class RpiwRoleSession(Base):
    """Tracks active user sessions with role context."""
    __tablename__ = "rpiw_role_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    role_code = Column(String, nullable=False)
    department = Column(String, nullable=True)
    active_workspace = Column(String, nullable=True)  # Current workspace view
    assigned_patients = Column(JSON, default=[])  # List of patient UHIDs
    session_token = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_activity = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)


class RpiwRoleComponent(Base):
    """Defines UI components available for each role."""
    __tablename__ = "rpiw_role_components"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_code = Column(String, nullable=False, index=True)
    component_key = Column(String, nullable=False)  # e.g. patient_summary_panel, vitals_panel
    component_label = Column(String, nullable=False)
    component_type = Column(String, default="panel")  # panel, widget, action_bar, nav_item
    component_config = Column(JSON, default={})  # Size, position, default state
    sort_order = Column(Integer, default=0)
    is_visible = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)


class RpiwRoleActivityLog(Base):
    """Immutable audit trail for all role-based activities."""
    __tablename__ = "rpiw_role_activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    role_code = Column(String, nullable=False)
    action = Column(String, nullable=False)  # e.g. recorded_vitals, created_order, collected_sample
    action_label = Column(String, nullable=True)
    patient_uhid = Column(String, nullable=True, index=True)
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    details = Column(JSON, default={})
    ip_address = Column(String, nullable=True)
    performed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
