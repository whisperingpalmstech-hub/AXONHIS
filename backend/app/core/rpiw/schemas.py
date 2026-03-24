from datetime import datetime, date
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional, List, Any


# User Role Schemas
class RpiwUserRoleCreate(BaseModel):
    user_id: UUID
    role_code: str
    role_label: str
    department: Optional[str] = None
    is_primary: bool = True
    assigned_by: Optional[str] = None

class RpiwUserRoleOut(BaseModel):
    id: UUID
    user_id: UUID
    role_code: str
    role_label: str
    department: Optional[str]
    is_primary: bool
    is_active: bool
    assigned_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Role Permission Schemas
class RpiwRolePermissionCreate(BaseModel):
    role_code: str
    permission_key: str
    permission_label: str
    resource_type: Optional[str] = None
    can_create: bool = False
    can_read: bool = True
    can_update: bool = False
    can_delete: bool = False

class RpiwRolePermissionOut(BaseModel):
    id: UUID
    role_code: str
    permission_key: str
    permission_label: str
    resource_type: Optional[str]
    can_create: bool
    can_read: bool
    can_update: bool
    can_delete: bool
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


# Role Workflow Schemas
class RpiwRoleWorkflowCreate(BaseModel):
    role_code: str
    workflow_key: str
    workflow_label: str
    workflow_description: Optional[str] = None
    sort_order: int = 0
    icon: Optional[str] = None
    route_path: Optional[str] = None

class RpiwRoleWorkflowOut(BaseModel):
    id: UUID
    role_code: str
    workflow_key: str
    workflow_label: str
    workflow_description: Optional[str]
    sort_order: int
    icon: Optional[str]
    route_path: Optional[str]
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


# Role Session Schemas
class RpiwRoleSessionOut(BaseModel):
    id: UUID
    user_id: UUID
    role_code: str
    department: Optional[str]
    active_workspace: Optional[str]
    assigned_patients: Any
    started_at: datetime
    last_activity: datetime
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


# Role Component Schemas
class RpiwRoleComponentCreate(BaseModel):
    role_code: str
    component_key: str
    component_label: str
    component_type: str = "panel"
    component_config: Any = {}
    sort_order: int = 0
    is_visible: bool = True

class RpiwRoleComponentOut(BaseModel):
    id: UUID
    role_code: str
    component_key: str
    component_label: str
    component_type: str
    component_config: Any
    sort_order: int
    is_visible: bool
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


# Activity Log Schemas
class RpiwActivityLogCreate(BaseModel):
    user_id: UUID
    role_code: str
    action: str
    action_label: Optional[str] = None
    patient_uhid: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Any = {}

class RpiwActivityLogOut(BaseModel):
    id: UUID
    user_id: UUID
    role_code: str
    action: str
    action_label: Optional[str]
    patient_uhid: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Any
    performed_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Composite response for workspace initialization
class RpiwWorkspaceConfig(BaseModel):
    role: RpiwUserRoleOut
    permissions: List[RpiwRolePermissionOut]
    workflows: List[RpiwRoleWorkflowOut]
    components: List[RpiwRoleComponentOut]
    session: Optional[RpiwRoleSessionOut] = None
