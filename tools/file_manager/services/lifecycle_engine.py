"""
Lifecycle Engine - Constraint rules for operations.

Provides:
  - LifecycleViolation exception with guidance
  - @lifecycle_constraint decorator for operation validation
  - BaseConstraintChecker for implementing constraint rules
"""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Optional, List


# =============================================================================
# Exceptions
# =============================================================================

class LifecycleViolation(Exception):
    """Raised when an operation violates lifecycle constraints."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        guidance: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.guidance = guidance or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
            "guidance": self.guidance,
        }


# =============================================================================
# Constraint Types
# =============================================================================

@dataclass
class ConstraintContext:
    """Context passed to constraint check functions."""
    user_id: str
    username: str
    role_name: str
    space_id: Optional[str] = None
    team_id: Optional[str] = None
    pool_id: Optional[str] = None
    resource_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.extra.get(key, default)


@dataclass
class ConstraintResult:
    """Result of a constraint check."""
    passed: bool
    reason: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    guidance: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def allow(cls, reason: str = "") -> "ConstraintResult":
        return cls(passed=True, reason=reason)

    @classmethod
    def deny(
        cls,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        guidance_action: Optional[str] = None,
        guidance_url: Optional[str] = None,
    ) -> "ConstraintResult":
        guidance = {}
        if guidance_action or guidance_url:
            guidance["action"] = guidance_action or ""
            guidance["url"] = guidance_url or ""
        return cls(
            passed=False,
            reason=message,
            details={"error_code": code, **(details or {})},
            guidance=guidance,
        )


@dataclass
class ConstraintRule:
    """A lifecycle constraint rule."""
    code: str
    check_fn: Callable[[ConstraintContext], ConstraintResult]
    error_message: str
    guidance_action: Optional[str] = None
    guidance_url: Optional[str] = None
    applies_to: Optional[List[str]] = None  # Operation names this applies to


# =============================================================================
# Decorator
# =============================================================================

def lifecycle_constraint(
    rule: ConstraintRule,
):
    """
    Decorator to apply a lifecycle constraint to an async function.

    Usage:
        @lifecycle_constraint(ConstraintRule(
            code="NOT_SPACE_MEMBER",
            check_fn=lambda ctx: check_membership(ctx),
            error_message="请先加入团队或空间才能上传文件",
            guidance_action="join_team",
            guidance_url="/teams",
        ))
        async def upload_file(ctx: ConstraintContext, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract ConstraintContext from args/kwargs
            ctx = _extract_context(args, kwargs)
            if ctx is None:
                # If no context found, try to get from first arg
                if args:
                    ctx = args[0]

            result = rule.check_fn(ctx)
            if not result.passed:
                raise LifecycleViolation(
                    code=rule.code,
                    message=result.reason or rule.error_message,
                    details=result.details,
                    guidance={
                        "action": rule.guidance_action or "",
                        "url": rule.guidance_url or "",
                    },
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def _extract_context(args, kwargs) -> Optional[ConstraintContext]:
    """Extract ConstraintContext from function args."""
    # Check kwargs first
    for key in ("ctx", "context", "user_ctx"):
        if key in kwargs:
            val = kwargs[key]
            if isinstance(val, ConstraintContext):
                return val
    # Check args
    for arg in args:
        if isinstance(arg, ConstraintContext):
            return arg
    return None


# =============================================================================
# Pre-built Constraint Rules
# =============================================================================

def check_no_teams_using_pool(pool_id: str) -> ConstraintRule:
    """Storage pool cannot be deleted if teams are using it."""
    def check(ctx: ConstraintContext) -> ConstraintResult:
        # Edge case: pool is being migrated
        if ctx.get("pool_migrating", False):
            return ConstraintResult.deny(
                code="POOL_MIGRATING",
                message="存储池正在迁移中，暂时无法删除",
                details={"pool_id": pool_id, "migration_progress": ctx.get("migration_progress", 0)},
                guidance_action="wait_migration",
                guidance_url=None
            )
        # Edge case: pool has teams with active operations
        if ctx.get("teams_with_active_ops", 0) > 0:
            return ConstraintResult.deny(
                code="POOL_HAS_ACTIVE_OPS",
                message=f"存储池有 {ctx.get('teams_with_active_ops')} 个团队正在执行操作，请稍后再试",
                details={"active_ops": ctx.get("teams_with_active_ops")},
                guidance_action="retry_later",
                guidance_url=None
            )
        # Check if any teams use this pool
        team_count = ctx.get("team_count", 0)
        if team_count > 0:
            team_names = ctx.get("team_names", [])[:3]
            msg = f"该存储池仍有 {team_count} 个团队使用"
            if team_names:
                msg += f"（{', '.join(team_names)}"
                if team_count > 3:
                    msg += f" 等{team_count}个"
                msg += "）"
            msg += "，无法删除"
            return ConstraintResult.deny(
                code="STORAGE_POOL_IN_USE",
                message=msg,
                details={"pool_id": pool_id, "team_count": team_count, "teams": team_names},
                guidance_action="view_teams",
                guidance_url=f"/admin/teams?pool_id={pool_id}"
            )
        return ConstraintResult.allow()
    return ConstraintRule(
        code="STORAGE_POOL_IN_USE",
        check_fn=check,
        error_message="该存储池仍有团队使用，无法删除",
        guidance_action="view_teams",
        guidance_url="/admin/pools",
    )


def _check_pool_in_use(ctx: ConstraintContext, pool_id: str) -> ConstraintResult:
    """Check if pool has any teams bound to it."""
    # Delegated to inline check in check_no_teams_using_pool
    return ConstraintResult.allow()


def check_space_has_no_members(space_id: str) -> ConstraintRule:
    """Space cannot be deleted if it still has members."""
    def check(ctx: ConstraintContext) -> ConstraintResult:
        # Edge case: space has pending share requests
        pending_shares = ctx.get("pending_share_requests", 0)
        if pending_shares > 0:
            return ConstraintResult.deny(
                code="SPACE_HAS_PENDING_SHARES",
                message=f"该空间有 {pending_shares} 个待处理的分享请求，请先处理后再删除",
                details={"pending_shares": pending_shares},
                guidance_action="view_shares",
                guidance_url=f"/spaces/{space_id}/shares"
            )
        # Edge case: space has pending transfer
        if ctx.get("transfer_pending", False):
            return ConstraintResult.deny(
                code="SPACE_TRANSFER_PENDING",
                message="空间转让处理中，暂时无法删除",
                details={"space_id": space_id},
                guidance_action="wait_transfer",
                guidance_url=None
            )
        member_count = ctx.get("member_count", 0)
        if member_count > 0:
            return ConstraintResult.deny(
                code="SPACE_HAS_MEMBERS",
                message=f"该空间仍有 {member_count} 个成员，无法删除",
                details={"space_id": space_id, "member_count": member_count},
                guidance_action="view_members",
                guidance_url=f"/spaces/{space_id}/members"
            )
        return ConstraintResult.allow()
    return ConstraintRule(
        code="SPACE_HAS_MEMBERS",
        check_fn=check,
        error_message="该空间仍有成员，无法删除",
        guidance_action="view_members",
        guidance_url="/spaces",
    )


def _check_space_members(ctx: ConstraintContext, space_id: str) -> ConstraintResult:
    """Check if space has any members."""
    # Delegated to inline check in check_space_has_no_members
    return ConstraintResult.allow()


def check_is_space_owner(space_id: str) -> ConstraintRule:
    """Only space owner can perform certain operations."""
    def check(ctx: ConstraintContext) -> ConstraintResult:
        if not ctx.get("is_owner", False):
            # Edge case: user is admin, grant temporary permission
            if ctx.get("is_admin", False):
                return ConstraintResult.allow(reason="Admin override for operation")
            return ConstraintResult.deny(
                code="NOT_SPACE_OWNER",
                message="只有空间所有者可以执行此操作",
                details={"space_id": space_id, "user_id": ctx.user_id},
                guidance_action="transfer_ownership",
                guidance_url=f"/spaces/{space_id}/settings"
            )
        return ConstraintResult.allow()
    return ConstraintRule(
        code="NOT_SPACE_OWNER",
        check_fn=check,
        error_message="只有空间所有者可以执行此操作",
        guidance_action="transfer_ownership",
        guidance_url="/spaces",
    )


def _check_owner(ctx: ConstraintContext, space_id: str) -> ConstraintResult:
    """Check if user is space owner."""
    # Delegated to inline check in check_is_space_owner
    return ConstraintResult.allow()


def check_has_available_pool() -> ConstraintRule:
    """User cannot create team if no storage pool is available."""
    def check(ctx: ConstraintContext) -> ConstraintResult:
        available_count = ctx.get("available_pools", 0)
        if available_count <= 0:
            return ConstraintResult.deny(
                code="NO_AVAILABLE_POOL",
                message="系统暂无可用存储池，无法创建新团队。请联系管理员创建存储池后再试。",
                details={"requested": ctx.get("requested_quota", 0)},
                guidance_action="create_pool",
                guidance_url="/admin/pools"
            )
        # Edge case: available pools are near capacity
        for pool in ctx.get("pools", []):
            if pool.get("available_bytes", 0) < ctx.get("requested_quota", 0):
                return ConstraintResult.deny(
                    code="POOL_CAPACITY_INSUFFICIENT",
                    message="可用存储池容量不足，请联系管理员扩容或等待资源释放",
                    details={"requested": ctx.requested_quota, "available": pool.get("available_bytes", 0)},
                    guidance_action="contact_admin",
                    guidance_url="/admin"
                )
        return ConstraintResult.allow()
    return ConstraintRule(
        code="NO_AVAILABLE_POOL",
        check_fn=check,
        error_message="系统暂无可用存储池，请联系管理员创建",
        guidance_action="create_pool",
        guidance_url="/admin/pools",
    )


def _check_available_pool(ctx: ConstraintContext) -> ConstraintResult:
    """Check if any storage pool is available."""
    # Delegated to inline check in check_has_available_pool
    return ConstraintResult.allow()


def check_is_team_member(team_id: str) -> ConstraintRule:
    """User must be a team member to create private space."""
    def check(ctx: ConstraintContext) -> ConstraintResult:
        if not ctx.get("is_member", False):
            # Edge case: user has pending invitation
            if ctx.get("has_pending_invitation", False):
                return ConstraintResult.deny(
                    code="INVITATION_PENDING",
                    message="您有待处理的邀请，请先接受或拒绝后再申请",
                    details={"team_id": team_id},
                    guidance_action="view_invitations",
                    guidance_url="/invitations"
                )
            return ConstraintResult.deny(
                code="NOT_TEAM_MEMBER",
                message="只有团队成员才能申请私人空间",
                details={"team_id": team_id},
                guidance_action="join_team",
                guidance_url="/teams"
            )
        # Edge case: user's membership is pending approval
        if ctx.get("member_status") == "pending":
            return ConstraintResult.deny(
                code="MEMBERSHIP_PENDING",
                message="您的成员资格正在等待审批，请耐心等待",
                details={"team_id": team_id},
                guidance_action="wait_approval",
                guidance_url=None
            )
        return ConstraintResult.allow()
    return ConstraintRule(
        code="NOT_TEAM_MEMBER",
        check_fn=check,
        error_message="只有团队成员才能申请私人空间",
        guidance_action="join_team",
        guidance_url="/teams",
    )


def _check_team_member(ctx: ConstraintContext, team_id: str) -> ConstraintResult:
    """Check if user is a member of the team."""
    # Delegated to inline check in check_is_team_member
    return ConstraintResult.allow()


def check_upload_constraints() -> ConstraintRule:
    """User must be a space member and have sufficient quota to upload."""
    def check(ctx: ConstraintContext) -> ConstraintResult:
        # Check if user is a member
        if not ctx.get("is_member", False):
            return ConstraintResult.deny(
                code="NOT_SPACE_MEMBER",
                message="请先加入团队或空间才能上传文件",
                details={"user_id": ctx.user_id},
                guidance_action="join_team",
                guidance_url="/teams"
            )
        # Check quota
        if not ctx.get("sufficient_quota", True):
            required = ctx.get("required_bytes", 0)
            available = ctx.get("available_bytes", 0)
            return ConstraintResult.deny(
                code="QUOTA_EXCEEDED",
                message=f"存储配额已用尽（已用 {required} 字节，可用 {available} 字节），无法上传新文件",
                details={"required_bytes": required, "available_bytes": available},
                guidance_action="view_trash",
                guidance_url="/trash"
            )
        return ConstraintResult.allow()
    return ConstraintRule(
        code="UPLOAD_CONSTRAINTS",
        check_fn=check,
        error_message="上传文件约束检查失败"
    )


def check_delete_team_constraints() -> ConstraintRule:
    """Only team owner can delete the team."""
    def check(ctx: ConstraintContext) -> ConstraintResult:
        if not ctx.get("is_owner", False):
            return ConstraintResult.deny(
                code="NOT_TEAM_OWNER",
                message="只有团队所有者可以删除团队",
                guidance_action="contact_admin",
                guidance_url="/admin"
            )
        # Edge case: team is being migrated
        if ctx.get("is_migrating", False):
            return ConstraintResult.deny(
                code="TEAM_MIGRATING",
                message="团队正在迁移中，暂时无法删除",
                details={"team_id": ctx.team_id, "migration_status": ctx.get("migration_status")},
                guidance_action="wait_migration",
                guidance_url=None
            )
        # Edge case: team has pending invitations
        if ctx.get("pending_invitations", 0) > 0:
            return ConstraintResult.deny(
                code="TEAM_HAS_PENDING_INVITATIONS",
                message=f"团队仍有 {ctx.get('pending_invitations')} 个待处理邀请，请先取消后再删除",
                details={"pending_count": ctx.get("pending_invitations")},
                guidance_action="cancel_invitations",
                guidance_url=None
            )
        return ConstraintResult.allow()
    return ConstraintRule(
        code="DELETE_TEAM_CONSTRAINTS",
        check_fn=check,
        error_message="删除团队约束检查失败"
    )


def check_update_quota_constraints() -> ConstraintRule:
    """Only space owner can update quota."""
    def check(ctx: ConstraintContext) -> ConstraintResult:
        if not ctx.get("is_owner", False):
            return ConstraintResult.deny(
                code="NOT_SPACE_OWNER",
                message="只有空间所有者可以修改配额",
                guidance_action="contact_admin",
                guidance_url="/admin"
            )
        # Edge case: new quota is less than current usage
        if ctx.get("new_quota", 0) < ctx.get("current_usage", 0):
            return ConstraintResult.deny(
                code="QUOTA_LESS_THAN_USAGE",
                message=f"新配额不能小于当前已用空间（当前已用 {ctx.get('current_usage')} 字节）",
                details={"new_quota": ctx.new_quota, "current_usage": ctx.current_usage},
                guidance_action="reduce_usage",
                guidance_url=None
            )
        return ConstraintResult.allow()
    return ConstraintRule(
        code="UPDATE_QUOTA_CONSTRAINTS",
        check_fn=check,
        error_message="更新配额约束检查失败"
    )


def check_join_team_constraints() -> ConstraintRule:
    """User must have a valid credential to join team."""
    def check(ctx: ConstraintContext) -> ConstraintResult:
        # Check credential validity
        if not ctx.get("credential_valid", False):
            expired = ctx.get("credential_expired", False)
            if expired:
                return ConstraintResult.deny(
                    code="CREDENTIAL_EXPIRED",
                    message="邀请码已过期，请联系管理员获取新的邀请链接",
                    guidance_action="contact_admin",
                    guidance_url="/admin"
                )
            return ConstraintResult.deny(
                code="INVALID_CREDENTIAL",
                message="邀请码无效，请检查链接是否正确",
                guidance_action="contact_admin",
                guidance_url="/admin"
            )
        # Edge case: user already a member
        if ctx.get("already_member", False):
            return ConstraintResult.deny(
                code="ALREADY_TEAM_MEMBER",
                message="您已经是该团队成员，无需重复加入",
                guidance_action="view_team",
                guidance_url=f"/teams/{ctx.team_id}"
            )
        # Edge case: team is inactive
        if not ctx.get("team_active", True):
            return ConstraintResult.deny(
                code="TEAM_INACTIVE",
                message="该团队已解散或处于非活跃状态，无法加入",
                guidance_action="view_teams",
                guidance_url="/teams"
            )
        # Edge case: user limit reached
        if ctx.get("member_count", 0) >= ctx.get("member_limit", float('inf')):
            return ConstraintResult.deny(
                code="MEMBER_LIMIT_REACHED",
                message="团队成员数已达上限，请联系管理员扩容",
                details={"current": ctx.member_count, "limit": ctx.member_limit},
                guidance_action="contact_admin",
                guidance_url="/admin"
            )
        return ConstraintResult.allow()
    return ConstraintRule(
        code="JOIN_TEAM_CONSTRAINTS",
        check_fn=check,
        error_message="加入团队约束检查失败"
    )


# =============================================================================
# Constraint Registry
# =============================================================================

class ConstraintRegistry:
    """
    Registry for lifecycle constraint rules.
    Operations can query this registry for applicable constraints.
    """

    def __init__(self):
        self._rules: Dict[str, List[ConstraintRule]] = {}

    def register(self, operation: str, rule: ConstraintRule) -> None:
        """Register a constraint rule for an operation."""
        if operation not in self._rules:
            self._rules[operation] = []
        self._rules[operation].append(rule)

    def get_constraints(self, operation: str) -> List[ConstraintRule]:
        """Get all constraint rules for an operation."""
        return self._rules.get(operation, [])

    def check_all(self, operation: str, ctx: ConstraintContext) -> List[ConstraintResult]:
        """Run all constraints for an operation, return results."""
        results = []
        for rule in self.get_constraints(operation):
            result = rule.check_fn(ctx)
            results.append(result)
        return results


# Global registry instance
_constraint_registry: Optional[ConstraintRegistry] = None


def get_constraint_registry() -> ConstraintRegistry:
    """Get the global constraint registry."""
    global _constraint_registry
    if _constraint_registry is None:
        _constraint_registry = ConstraintRegistry()
        _register_default_constraints()
    return _constraint_registry


def _register_default_constraints() -> None:
    """Register default constraint rules."""
    registry = _constraint_registry

    # Pool deletion constraints
    registry.register("delete_pool", check_no_teams_using_pool(""))

    # Space deletion constraints
    registry.register("delete_space", check_space_has_no_members(""))

    # Member operations
    registry.register("invite_member", check_is_space_owner(""))
    registry.register("remove_member", check_is_space_owner(""))

    # Team operations
    registry.register("create_team", check_has_available_pool())
    registry.register("delete_team", check_delete_team_constraints())
    registry.register("join_team", check_join_team_constraints())

    # Space operations
    registry.register("create_private_space", check_is_team_member(""))
    registry.register("update_quota", check_update_quota_constraints())

    # File operations
    registry.register("upload_file", check_upload_constraints())


# =============================================================================
# RBAC Permission Constraints (T2 Integration)
# =============================================================================

def check_rbac_permission(resource: str, action: str) -> ConstraintRule:
    """
    Create a constraint rule that checks RBAC permission.

    Args:
        resource: Resource type (file, space, team, user, role, storage_pool)
        action: Action type (create, read, update, delete, manage)

    Usage:
        registry.register("create_space", check_rbac_permission("space", "create"))
    """
    def check_fn(ctx: ConstraintContext) -> ConstraintResult:
        # Admin bypass
        if ctx.role_name == "admin":
            return ConstraintResult.allow("Admin bypass")

        # Check if user has the required permission in extra
        required_perm = f"{resource}:{action}"
        user_perms = ctx.get("rbac_permissions", [])

        if required_perm in user_perms:
            return ConstraintResult.allow(f"Permission '{required_perm}' granted")

        # Check wildcard
        if f"{resource}:*" in user_perms:
            return ConstraintResult.allow(f"Wildcard permission '{resource}:*' granted")

        if "*:*" in user_perms:
            return ConstraintResult.allow("Full wildcard '*:*' granted")

        return ConstraintResult.deny(
            code="PERMISSION_DENIED",
            message=f"No permission for '{action}' on '{resource}'",
            details={"required": required_perm},
            guidance_action="contact_admin",
            guidance_url="/admin",
        )

    return ConstraintRule(
        code="PERMISSION_DENIED",
        check_fn=check_fn,
        error_message=f"No permission for '{action}' on '{resource}'",
        guidance_action="contact_admin",
        guidance_url="/admin",
        applies_to=[f"{resource}:{action}"],
    )


def register_rbac_constraint(registry: ConstraintRegistry, operation: str, resource: str, action: str) -> None:
    """Register an RBAC permission constraint for an operation."""
    registry.register(operation, check_rbac_permission(resource, action))
