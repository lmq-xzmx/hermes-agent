"""
Data Transfer Objects (DTOs) - Request and Response models for the API.

These are pure Pydantic models with no ORM dependencies.
They define the contract between HTTP layer and service layer.
"""

from __future__ import annotations

from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field


# =============================================================================
# Auth DTOs
# =============================================================================

class LoginRequestDTO(BaseModel):
    username: str
    password: str


class RegisterRequestDTO(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role_id: Optional[str] = None


class RefreshRequestDTO(BaseModel):
    access_token: str
    refresh_token: str


class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponseDTO(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role_id: Optional[str] = None
    role_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class LoginResponseDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponseDTO


# =============================================================================
# File DTOs
# =============================================================================

class FileItemDTO(BaseModel):
    name: str
    path: str
    is_directory: bool
    size: int
    modified: Optional[datetime] = None
    created: Optional[datetime] = None
    permissions: str = ""


class FileListResponseDTO(BaseModel):
    path: str
    items: List[FileItemDTO] = []
    total: int
    readable: bool


class FileContentResponseDTO(BaseModel):
    path: str
    content: str
    size: int
    encoding: str


class FileWriteRequestDTO(BaseModel):
    path: str
    content: str
    overwrite: bool = True


class FileReadRequestDTO(BaseModel):
    path: str
    offset: int = 0
    size: Optional[int] = None
    encoding: str = "utf-8"


class FileDeleteRequestDTO(BaseModel):
    path: str
    recursive: bool = False


class MkDirRequestDTO(BaseModel):
    path: str


class FileCopyRequestDTO(BaseModel):
    from_path: str
    to_path: str
    overwrite: bool = False


class FileMoveRequestDTO(BaseModel):
    from_path: str
    to_path: str
    overwrite: bool = False


class FileStatResponseDTO(BaseModel):
    name: str
    path: str
    is_directory: bool
    size: int
    modified: Optional[datetime] = None
    created: Optional[datetime] = None
    permissions: str = ""


# =============================================================================
# Share DTOs
# =============================================================================

class CreateShareRequestDTO(BaseModel):
    path: str
    password: Optional[str] = None
    permissions: str = "read"
    expires_in_days: Optional[int] = None
    max_access_count: Optional[int] = None


class ShareLinkResponseDTO(BaseModel):
    token: str
    path: str
    permissions: str
    has_password: bool
    expires_at: Optional[datetime] = None
    max_access_count: Optional[int] = None
    access_count: int = 0
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None


# =============================================================================
# Admin DTOs
# =============================================================================

class CreateUserRequestDTO(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role_id: Optional[str] = None


class CreateRuleRequestDTO(BaseModel):
    role_id: str
    path_pattern: str
    permissions: str  # e.g. "read,write,delete"
    priority: int = 0


class AuditQueryRequestDTO(BaseModel):
    user_id: Optional[str] = None
    action: Optional[str] = None
    path: Optional[str] = None
    result: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 100
    offset: int = 0


class AuditLogEntryDTO(BaseModel):
    id: str
    timestamp: datetime
    action: str
    result: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    path: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    extra: Optional[dict] = None


class AuditQueryResponseDTO(BaseModel):
    logs: List[AuditLogEntryDTO] = []
    total: int


class UserListItemDTO(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role_id: Optional[str] = None
    role_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class RoleDTO(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    permission_rules: List[str] = []


class UserListResponseDTO(BaseModel):
    users: List[UserListItemDTO] = []
    total: int


# =============================================================================
# Generic DTOs
# =============================================================================

class MessageResponseDTO(BaseModel):
    message: str


class ErrorResponseDTO(BaseModel):
    detail: str
