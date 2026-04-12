"""Auth schemas – enhanced request/response models for Phase 1."""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── User Schemas ──────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = None
    role_ids: list[uuid.UUID] = Field(default_factory=list)


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    status: str | None = None


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    full_name: str
    phone: str | None
    status: str
    last_login_at: datetime | None
    two_factor_enabled: bool
    created_at: datetime
    roles: list["RoleOut"] = []

    model_config = {"from_attributes": True}


class UserListOut(BaseModel):
    total: int
    items: list[UserOut]


# ── Auth Schemas ──────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_name: str | None = None
    device_type: str | None = "web"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


# ── Role Schemas ──────────────────────────────────────────────────────────

class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    display_name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    permission_ids: list[uuid.UUID] = Field(default_factory=list)


class RoleOut(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str
    description: str | None
    is_system: bool
    permissions: list["PermissionOut"] = []

    model_config = {"from_attributes": True}


# ── Permission Schemas ────────────────────────────────────────────────────

class PermissionOut(BaseModel):
    id: uuid.UUID
    code: str
    display_name: str
    category: str
    description: str | None

    model_config = {"from_attributes": True}


# ── Session Schemas ───────────────────────────────────────────────────────

class DeviceSessionOut(BaseModel):
    id: uuid.UUID
    device_name: str | None
    device_type: str | None
    ip_address: str | None
    is_active: bool
    last_used_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
