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
    export_format: Optional[str] = None  # "csv" | "json" | None (default: json)


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


# =============================================================================
# Space DTOs
# =============================================================================

class CreateSpaceRequestDTO(BaseModel):
    name: str
    storage_pool_id: str
    parent_id: Optional[str] = None
    max_bytes: int = 0
    space_type: str = "team"  # "root" | "team" | "private"
    description: Optional[str] = None


class UpdateSpaceRequestDTO(BaseModel):
    name: Optional[str] = None
    max_bytes: Optional[int] = None
    status: Optional[str] = None


class SpaceMemberDTO(BaseModel):
    id: str
    space_id: str
    user_id: str
    username: Optional[str] = None
    role: str  # "owner" | "member" | "viewer"
    quota_bytes: int = 0
    status: str = "active"
    joined_at: Optional[datetime] = None


class SpaceDTO(BaseModel):
    id: str
    name: str
    parent_id: Optional[str] = None
    storage_pool_id: str
    pool_name: Optional[str] = None
    owner_id: str
    owner_name: Optional[str] = None
    max_bytes: int = 0
    used_bytes: int = 0
    space_type: str = "team"
    status: str = "active"
    description: Optional[str] = None
    members: List[SpaceMemberDTO] = []
    created_at: Optional[datetime] = None


class SpaceListResponseDTO(BaseModel):
    spaces: List[SpaceDTO] = []
    total: int


class CreateCredentialRequestDTO(BaseModel):
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None


class CredentialDTO(BaseModel):
    id: str
    space_id: str
    space_name: Optional[str] = None
    token: Optional[str] = None  # Only included when created
    max_uses: Optional[int] = None
    used_count: int = 0
    expires_at: Optional[datetime] = None
    created_by: Optional[str] = None
    is_active: bool = True
    is_valid: bool = True
    created_at: Optional[datetime] = None


class JoinSpaceRequestDTO(BaseModel):
    token: str


class CreatePrivateSpaceRequestDTO(BaseModel):
    """Request to create a private sub-space within a parent space."""
    requested_name: str
    requested_bytes: int = 0
    reason: Optional[str] = None


class SpaceRequestDTO(BaseModel):
    id: str
    space_id: str
    space_name: Optional[str] = None
    requester_id: str
    requester_name: Optional[str] = None
    requested_name: str
    requested_bytes: int = 0
    reason: Optional[str] = None
    status: str = "pending"
    reviewed_by: Optional[str] = None
    reviewer_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    created_at: Optional[datetime] = None


class ApproveRejectRequestDTO(BaseModel):
    status: str  # "approved" | "rejected"
    note: Optional[str] = None


class FileVersionDTO(BaseModel):
    id: str
    space_id: str
    path: str
    name: str
    is_directory: bool = False
    size: int = 0
    checksum: Optional[str] = None
    version: int
    action: str  # "create" | "update" | "delete" | "restore"
    created_by: Optional[str] = None
    creator_name: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[dict] = None


class FileVersionListResponseDTO(BaseModel):
    versions: List[FileVersionDTO] = []
    total: int


class RestoreVersionRequestDTO(BaseModel):
    version: int


class StoragePoolDTO(BaseModel):
    id: str
    name: str
    base_path: str
    protocol: str = "local"
    total_bytes: int = 0
    free_bytes: int = 0
    is_active: bool = True
    description: Optional[str] = None
    created_at: Optional[datetime] = None


# =============================================================================
# Workflow DTOs
# =============================================================================

class WorkflowStepDTO(BaseModel):
    id: str
    workflow_id: str
    order: int
    command: str
    explanation: Optional[str] = None
    confirm_required: bool = False
    created_at: Optional[datetime] = None


class CreateWorkflowStepRequestDTO(BaseModel):
    order: int
    command: str
    explanation: Optional[str] = None
    confirm_required: bool = False


class CreateWorkflowRequestDTO(BaseModel):
    name: str
    description: Optional[str] = None
    is_shared: bool = False
    tags: List[str] = []
    steps: List[CreateWorkflowStepRequestDTO] = []


class UpdateWorkflowRequestDTO(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_shared: Optional[bool] = None
    tags: Optional[List[str]] = None


class WorkflowDTO(BaseModel):
    id: str
    space_id: str
    owner_id: str
    owner_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    is_shared: bool = False
    tags: List[str] = []
    usage_count: int = 0
    step_count: int = 0
    created_at: Optional[datetime] = None


class WorkflowDetailDTO(WorkflowDTO):
    steps: List[WorkflowStepDTO] = []


class WorkflowListResponseDTO(BaseModel):
    workflows: List[WorkflowDTO] = []
    total: int


class ReorderStepsRequestDTO(BaseModel):
    step_ids: List[str]


class DuplicateWorkflowRequestDTO(BaseModel):
    new_name: Optional[str] = None


class ExecuteWorkflowRequestDTO(BaseModel):
    variables: dict = {}


# =============================================================================
# Notebook DTOs
# =============================================================================

class NotebookVariableDTO(BaseModel):
    id: str
    notebook_id: str
    name: str
    default_value: Optional[str] = None
    description: Optional[str] = None
    is_required: bool = True


class CreateNotebookVariableRequestDTO(BaseModel):
    name: str
    default_value: Optional[str] = None
    description: Optional[str] = None
    is_required: bool = True


class CreateNotebookRequestDTO(BaseModel):
    name: str
    description: Optional[str] = None
    content: str  # Markdown
    is_shared: bool = False
    tags: List[str] = []
    variables: List[CreateNotebookVariableRequestDTO] = []


class UpdateNotebookRequestDTO(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    is_shared: Optional[bool] = None
    tags: Optional[List[str]] = None


class NotebookDTO(BaseModel):
    id: str
    space_id: str
    owner_id: str
    owner_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    content: Optional[str] = None  # May be omitted in list view
    is_shared: bool = False
    tags: List[str] = []
    usage_count: int = 0
    variable_count: int = 0
    created_at: Optional[datetime] = None


class NotebookDetailDTO(NotebookDTO):
    content: str  # Full content in detail view
    variables: List[NotebookVariableDTO] = []


class NotebookListResponseDTO(BaseModel):
    notebooks: List[NotebookDTO] = []
    total: int


class DuplicateNotebookRequestDTO(BaseModel):
    new_name: Optional[str] = None
