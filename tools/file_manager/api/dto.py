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
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)


class RegisterRequestDTO(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    email: Optional[str] = Field(None, max_length=256)
    role_id: Optional[str] = Field(None, max_length=64)


class RefreshRequestDTO(BaseModel):
    access_token: str = Field(..., min_length=1)
    refresh_token: str = Field(..., min_length=1)


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
    name: str = Field(..., min_length=1, max_length=256)
    path: str = Field(..., min_length=1, max_length=4096)
    is_directory: bool
    size: int = Field(..., ge=0)
    modified: Optional[datetime] = None
    created: Optional[datetime] = None
    permissions: str = ""


class FileListResponseDTO(BaseModel):
    path: str = Field(..., min_length=1, max_length=4096)
    items: List[FileItemDTO] = []
    total: int = Field(..., ge=0)
    readable: bool


class FileContentResponseDTO(BaseModel):
    path: str
    content: str
    size: int = Field(..., ge=0)
    encoding: str


class FileWriteRequestDTO(BaseModel):
    path: str = Field(..., min_length=1, max_length=4096)
    content: str
    overwrite: bool = True


class FileReadRequestDTO(BaseModel):
    path: str = Field(..., min_length=1, max_length=4096)
    offset: int = Field(default=0, ge=0)
    size: Optional[int] = Field(None, ge=1, le=10*1024*1024)  # Max 10MB
    encoding: str = "utf-8"


class FileDeleteRequestDTO(BaseModel):
    path: str = Field(..., min_length=1, max_length=4096)
    recursive: bool = False


class MkDirRequestDTO(BaseModel):
    path: str = Field(..., min_length=1, max_length=4096)


class FileCopyRequestDTO(BaseModel):
    from_path: str = Field(..., min_length=1, max_length=4096)
    to_path: str = Field(..., min_length=1, max_length=4096)
    overwrite: bool = False


class FileMoveRequestDTO(BaseModel):
    from_path: str = Field(..., min_length=1, max_length=4096)
    to_path: str = Field(..., min_length=1, max_length=4096)
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


# =============================================================================
# RBAC Permission DTOs (T3)
# =============================================================================

class CreatePermissionRequestDTO(BaseModel):
    """Request to create a new RBAC permission."""
    resource: str  # e.g. "file", "space", "team", "user", "role", "storage_pool"
    action: str     # e.g. "create", "read", "update", "delete", "manage"
    description: Optional[str] = None


class CreateRolePermissionRequestDTO(BaseModel):
    """Request to assign a permission to a role."""
    permission_id: str


class AssignRoleRequestDTO(BaseModel):
    """Request to assign a role to a user."""
    role_id: str


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


# =============================================================================
# Admin Analytics DTOs
# =============================================================================

class StoragePoolAnalyticsDTO(BaseModel):
    id: str
    name: str
    protocol: str
    base_path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_rate: float
    team_count: int
    space_count: int
    status: str  # "normal" | "warning" | "critical"


class StoragePoolsResponseDTO(BaseModel):
    pools: List[StoragePoolAnalyticsDTO] = []
    summary: dict


class UserSpaceNodeDTO(BaseModel):
    id: str
    name: str
    type: str  # "user" | "team" | "space"
    role: Optional[str] = None


class UserSpaceLinkDTO(BaseModel):
    source: str
    target: str
    value: float
    role: Optional[str] = None


class UserSpacesResponseDTO(BaseModel):
    nodes: List[UserSpaceNodeDTO] = []
    links: List[UserSpaceLinkDTO] = []
    stats: dict


class QuotaHeatmapEntryDTO(BaseModel):
    space_id: str
    space_name: str
    usage_rate: float
    status: str  # "normal" | "warning" | "critical"


class QuotaHeatmapTeamDTO(BaseModel):
    team_id: str
    team_name: str
    spaces: List[QuotaHeatmapEntryDTO] = []


class QuotaHeatmapResponseDTO(BaseModel):
    heatmap: List[QuotaHeatmapTeamDTO] = []
    legend: dict


class OperationTrendSeriesDTO(BaseModel):
    name: str
    data: List[int] = []


class OperationTrendsResponseDTO(BaseModel):
    dates: List[str] = []
    series: List[OperationTrendSeriesDTO] = []


class ActiveUserDTO(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    action_count: int
    last_action: Optional[datetime] = None


class ActiveUsersResponseDTO(BaseModel):
    users: List[ActiveUserDTO] = []
    total: int


class AlertDTO(BaseModel):
    id: str
    type: str
    level: str  # "info" | "warning" | "critical"
    resource: str
    resource_id: str
    resource_name: str
    message: str
    usage_rate: Optional[float] = None
    created_at: Optional[datetime] = None


class RecentActivityDTO(BaseModel):
    id: str
    user_id: str
    username: Optional[str] = None
    action: str
    target: str
    target_name: Optional[str] = None
    result: str
    created_at: Optional[datetime] = None


class AnalyticsOverviewResponseDTO(BaseModel):
    total_users: int
    active_users_7d: int
    new_users_7d: int
    total_teams: int
    total_spaces: int
    total_pools: int
    storage: dict
    alerts: List[AlertDTO] = []
    recent_activities: List[RecentActivityDTO] = []


# =============================================================================
# Hermes DTOs
# =============================================================================

class HermesExecuteRequestDTO(BaseModel):
    """Hermes 任务执行请求"""
    command: str = Field(..., description="Hermes 命令（如 execute, query, cron.list）")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="命令参数")
    priority: str = Field(default="normal", description="优先级: low, normal, high")
    callback_url: Optional[str] = Field(None, description="完成后回调的 Webhook URL")
    team_id: Optional[str] = Field(None, description="团队 ID（可选，不填则使用默认团队）")


class HermesTaskResponseDTO(BaseModel):
    """Hermes 任务响应"""
    id: str
    user_id: str
    team_id: str
    command: str
    params: Dict[str, Any]
    status: str
    priority: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    callback_url: Optional[str] = None


class HermesTaskListResponseDTO(BaseModel):
    """Hermes 任务列表响应"""
    tasks: List[HermesTaskResponseDTO] = []
    total: int


class HermesStatusResponseDTO(BaseModel):
    """Hermes 服务状态响应"""
    queue_size: int
    pending: int
    running: int
    completed: int
    failed: int
    total: int
    running_state: bool


class HermesCallbackDTO(BaseModel):
    """Hermes 任务完成回调"""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    completed_at: Optional[str] = None
