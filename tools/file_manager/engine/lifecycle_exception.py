"""
Lifecycle constraint exceptions and guidance actions.

Provides structured error responses with user guidance for lifecycle violations.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(Enum):
    """Lifecycle error codes."""
    # Storage Pool
    POOL_NOT_FOUND = "POOL_NOT_FOUND"
    POOL_IN_USE = "STORAGE_POOL_IN_USE"
    POOL_INACTIVE = "STORAGE_POOL_INACTIVE"
    NO_AVAILABLE_POOL = "NO_AVAILABLE_POOL"

    # Space
    SPACE_NOT_FOUND = "SPACE_NOT_FOUND"
    SPACE_HAS_MEMBERS = "SPACE_HAS_MEMBERS"
    NOT_SPACE_OWNER = "NOT_SPACE_OWNER"
    NOT_SPACE_MEMBER = "NOT_SPACE_MEMBER"
    SPACE_QUOTA_EXCEEDED = "SPACE_QUOTA_EXCEEDED"

    # Team
    TEAM_NOT_FOUND = "TEAM_NOT_FOUND"
    NOT_TEAM_OWNER = "NOT_TEAM_OWNER"
    MEMBER_LIMIT_EXCEEDED = "MEMBER_LIMIT_EXCEEDED"
    TEAM_QUOTA_EXCEEDED = "TEAM_QUOTA_EXCEEDED"

    # Credential
    INVALID_CREDENTIAL = "INVALID_CREDENTIAL"
    CREDENTIAL_EXPIRED = "CREDENTIAL_EXPIRED"
    CREDENTIAL_USED_UP = "CREDENTIAL_USED_UP"

    # General
    LIFECYCLE_VIOLATION = "LIFECYCLE_VIOLATION"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"


@dataclass
class GuidanceAction:
    """User guidance for resolving a lifecycle violation."""
    label: str                          # Button text
    icon: str = ""                      # Icon emoji
    action_type: str = "navigate"       # navigate | callback | modal
    path: Optional[str] = None           # Navigation path
    callback: Optional[str] = None       # Callback function name
    modal_config: Optional[Dict] = None  # Modal configuration


@dataclass
class LifecycleViolation(Exception):
    """
    Lifecycle constraint violation exception.

    Contains user-friendly error message and guidance action.
    """
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    guidance: Optional[GuidanceAction] = None
    http_status: int = 403

    def __post_init__(self):
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response format."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "guidance": {
                    "label": self.guidance.label if self.guidance else None,
                    "icon": self.guidance.icon if self.guidance else None,
                    "action_type": self.guidance.action_type if self.guidance else None,
                    "path": self.guidance.path if self.guidance else None,
                    "callback": self.guidance.callback if self.guidance else None,
                }
            }
        }

    # -------------------------------------------------------------------------
    # Factory methods for common violations
    # -------------------------------------------------------------------------

    @classmethod
    def not_space_member(cls, user_id: str, space_id: str) -> "LifecycleViolation":
        return cls(
            code=ErrorCode.NOT_SPACE_MEMBER.value,
            message="您还没有加入任何团队，无法访问文件存储。请先加入一个团队或创建一个新团队。",
            details={"user_id": user_id, "space_id": space_id},
            guidance=GuidanceAction(
                label="加入团队",
                icon="👥",
                action_type="navigate",
                path="/teams"
            )
        )

    @classmethod
    def pool_in_use(cls, pool_id: str, teams: list) -> "LifecycleViolation":
        team_names = ", ".join([t.get("name", "未知") for t in teams[:3]])
        if len(teams) > 3:
            team_names += f" 等 {len(teams)} 个团队"
        return cls(
            code=ErrorCode.POOL_IN_USE.value,
            message=f"该存储池仍被以下团队使用：{team_names}，无法删除。请先将团队迁移到其他存储池。",
            details={"pool_id": pool_id, "teams": teams},
            guidance=GuidanceAction(
                label="查看团队",
                icon="👥",
                action_type="navigate",
                path=f"/admin/teams?pool_id={pool_id}"
            ),
            http_status=409
        )

    @classmethod
    def quota_exceeded(cls, space_name: str, used: int, max: int, required: int) -> "LifecycleViolation":
        used_pct = (used / max * 100) if max > 0 else 0
        return cls(
            code=ErrorCode.SPACE_QUOTA_EXCEEDED.value,
            message=f"空间「{space_name}」配额已用尽（{used_pct:.0f}%），无法上传新文件。请清理回收站或联系管理员申请扩容。",
            details={"space_name": space_name, "used_bytes": used, "max_bytes": max, "required_bytes": required},
            guidance=GuidanceAction(
                label="查看回收站",
                icon="🗑️",
                action_type="navigate",
                path="/trash"
            )
        )

    @classmethod
    def team_quota_exceeded(cls, team_name: str, used: int, max: int, required: int) -> "LifecycleViolation":
        used_pct = (used / max * 100) if max > 0 else 0
        return cls(
            code=ErrorCode.TEAM_QUOTA_EXCEEDED.value,
            message=f"团队「{team_name}」配额已用尽（{used_pct:.0f}%），无法写入新文件。",
            details={"team_name": team_name, "used_bytes": used, "max_bytes": max, "required_bytes": required},
            guidance=GuidanceAction(
                label="查看团队",
                icon="👥",
                action_type="navigate",
                path="/teams"
            )
        )

    @classmethod
    def pool_out_of_space(cls, required: int, available: int) -> "LifecycleViolation":
        return cls(
            code=ErrorCode.POOL_INACTIVE.value,
            message=f"存储池空间不足。需要 {required} 字节，可用 {available} 字节。",
            details={"required_bytes": required, "available_bytes": available},
            guidance=GuidanceAction(
                label="联系管理员",
                icon="📧",
                action_type="callback",
                callback="showContactAdminModal"
            ),
            http_status=507
        )

    @classmethod
    def not_team_owner(cls) -> "LifecycleViolation":
        return cls(
            code=ErrorCode.NOT_TEAM_OWNER.value,
            message="只有团队所有者可以执行此操作。",
            guidance=GuidanceAction(
                label="联系管理员",
                icon="📧",
                action_type="callback",
                callback="showContactAdminModal"
            )
        )

    @classmethod
    def not_space_owner(cls) -> "LifecycleViolation":
        return cls(
            code=ErrorCode.NOT_SPACE_OWNER.value,
            message="只有空间所有者可以执行此操作。",
            guidance=GuidanceAction(
                label="联系管理员",
                icon="📧",
                action_type="callback",
                callback="showContactAdminModal"
            )
        )

    @classmethod
    def no_available_pool(cls) -> "LifecycleViolation":
        return cls(
            code=ErrorCode.NO_AVAILABLE_POOL.value,
            message="系统暂无可用存储池，无法创建新团队。请联系超级管理员创建存储池后再试。",
            guidance=GuidanceAction(
                label="联系管理员",
                icon="📧",
                action_type="callback",
                callback="showContactAdminModal"
            )
        )

    @classmethod
    def credential_expired(cls) -> "LifecycleViolation":
        return cls(
            code=ErrorCode.CREDENTIAL_EXPIRED.value,
            message="邀请码已过期，请联系管理员获取新链接。",
            guidance=GuidanceAction(
                label="返回",
                icon="🔙",
                action_type="navigate",
                path="/teams"
            ),
            http_status=410
        )

    @classmethod
    def space_has_members(cls, member_count: int) -> "LifecycleViolation":
        return cls(
            code=ErrorCode.SPACE_HAS_MEMBERS.value,
            message=f"该空间仍有 {member_count} 个成员，无法删除。请先移除所有成员。",
            details={"member_count": member_count},
            guidance=GuidanceAction(
                label="查看成员",
                icon="👥",
                action_type="navigate",
                path="/space/members"
            ),
            http_status=409
        )


# Singleton accessor for the global engine instance
_lifecycle_engine = None


def get_lifecycle_engine():
    """Get the global LifecycleEngine instance."""
    global _lifecycle_engine
    if _lifecycle_engine is None:
        from .lifecycle_engine import LifecycleEngine
        _lifecycle_engine = LifecycleEngine()
    return _lifecycle_engine


def set_lifecycle_engine(engine):
    """Set the global LifecycleEngine instance (for testing)."""
    global _lifecycle_engine
    _lifecycle_engine = engine