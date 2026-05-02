"""
Lifecycle constraint engine.

Provides declarative constraint checking with user guidance for violations.
"""

from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from .lifecycle_exception import LifecycleViolation, GuidanceAction


class ConstraintType(Enum):
    """Types of lifecycle constraints."""
    PRE_CHECK = "pre_check"          # Pre-condition check
    MUTEX = "mutex"                  # Mutual exclusion check
    STATE = "state"                   # State check
    QUOTA = "quota"                   # Quota check
    PERMISSION = "permission"         # Permission check


@dataclass
class ConstraintRule:
    """Definition of a lifecycle constraint rule."""
    code: str                           # Error code
    name: str                           # Human-readable name
    constraint_type: ConstraintType     # Type of constraint
    check_fn: Callable[[Any], bool]     # Check function
    error_message: str                 # Error message
    guidance: Dict[str, str] = field(default_factory=dict)  # Guidance action config
    priority: int = 0                  # Priority (lower = higher priority)


class LifecycleEngine:
    """
    Lifecycle constraint engine.

    Manages constraint rules and checks them before operations.
    """

    def __init__(self):
        self._rules: Dict[str, ConstraintRule] = {}
        self._action_rules: Dict[str, List[ConstraintRule]] = {}
        self._init_default_rules()

    def _init_default_rules(self):
        """Initialize default constraint rules."""
        self._register_default("STORAGE_POOL_IN_USE", ConstraintType.PRE_CHECK,
            lambda ctx: ctx.get("team_count", 0) == 0,
            "该存储池仍有团队使用，无法删除",
            {"label": "查看团队", "path": "/admin/teams"}
        )

        self._register_default("NOT_SPACE_MEMBER", ConstraintType.PRE_CHECK,
            lambda ctx: ctx.get("is_member", False),
            "请先加入团队或空间才能上传文件",
            {"label": "加入团队", "path": "/teams"}
        )

        self._register_default("NOT_TEAM_MEMBER", ConstraintType.PRE_CHECK,
            lambda ctx: ctx.get("is_member", False),
            "请先加入团队才能进行此操作",
            {"label": "加入团队", "path": "/teams"}
        )

        self._register_default("NO_AVAILABLE_POOL", ConstraintType.PRE_CHECK,
            lambda ctx: ctx.get("available_pools", 0) > 0,
            "系统暂无可用存储池，请联系管理员创建",
            {"label": "联系管理员", "action": "contact_admin"}
        )

        self._register_default("QUOTA_SUFFICIENT", ConstraintType.QUOTA,
            lambda ctx: ctx.get("sufficient_quota", True),
            "存储配额已用尽，无法上传新文件",
            {"label": "查看回收站", "path": "/trash"}
        )

        self._register_default("NOT_SPACE_OWNER", ConstraintType.PERMISSION,
            lambda ctx: ctx.get("is_owner", False),
            "只有空间所有者可以邀请成员",
            {"label": "联系管理员", "action": "contact_admin"}
        )

        self._register_default("NOT_TEAM_OWNER", ConstraintType.PERMISSION,
            lambda ctx: ctx.get("is_owner", False),
            "只有团队所有者可以执行此操作",
            {"label": "联系管理员", "action": "contact_admin"}
        )

        self._register_default("CREDENTIAL_VALID", ConstraintType.PRE_CHECK,
            lambda ctx: ctx.get("is_valid", False) is not False,
            "邀请码已过期或无效",
            {"label": "返回", "path": "/teams"}
        )

        self._register_default("SPACE_NO_MEMBERS", ConstraintType.PRE_CHECK,
            lambda ctx: ctx.get("member_count", 0) == 0,
            "该空间仍有成员，无法删除",
            {"label": "查看成员", "path": "/space/members"}
        )

    def _register_default(self, code: str, constraint_type: ConstraintType,
                          check_fn: Callable, error_message: str,
                          guidance: Dict[str, str], priority: int = 0):
        """Register a default constraint rule."""
        rule = ConstraintRule(
            code=code,
            name=code,
            constraint_type=constraint_type,
            check_fn=check_fn,
            error_message=error_message,
            guidance=guidance,
            priority=priority,
        )
        self.register_rule(rule)

    def register_rule(self, rule: ConstraintRule):
        """Register a constraint rule."""
        self._rules[rule.code] = rule

    def register_action_rule(self, action: str, rule_code: str):
        """Associate a rule with a specific action."""
        if action not in self._action_rules:
            self._action_rules[action] = []
        if rule_code in self._rules:
            self._action_rules[action].append(self._rules[rule_code])

    def check(self, action: str, context: Dict[str, Any]) -> Optional[ConstraintRule]:
        """
        Check if an action is allowed given the context.

        Returns:
            None if the check passes.
            ConstraintRule if the check fails.
        """
        rules = self._action_rules.get(action, [])
        for rule in sorted(rules, key=lambda r: r.priority):
            try:
                if not rule.check_fn(context):
                    return rule
            except Exception:
                # If check_fn raises, treat as pass to avoid blocking operations
                pass
        return None

    def raise_if_violated(self, action: str, context: Dict[str, Any]):
        """
        Check constraints and raise LifecycleViolation if any fail.

        Args:
            action: The action being performed.
            context: Context data for constraint evaluation.

        Raises:
            LifecycleViolation: If any constraint is violated.
        """
        violated_rule = self.check(action, context)
        if violated_rule:
            guidance_config = violated_rule.guidance
            action_type = "navigate" if guidance_config.get("path") else "callback"

            guidance = GuidanceAction(
                label=guidance_config.get("label", "确定"),
                icon=guidance_config.get("icon", ""),
                action_type=action_type,
                path=guidance_config.get("path"),
                callback=guidance_config.get("action"),
            )

            raise LifecycleViolation(
                code=violated_rule.code,
                message=violated_rule.error_message,
                guidance=guidance
            )

    def check_membership(self, user_id: str, space_id: str, db_factory) -> bool:
        """
        Check if a user is a member of a space/team.

        Args:
            user_id: The user ID.
            space_id: The space/team ID.
            db_factory: Database session factory.

        Returns:
            True if user is a member, False otherwise.
        """
        from .models import SpaceMember
        session = db_factory()
        try:
            member = session.query(SpaceMember).filter(
                SpaceMember.space_id == space_id,
                SpaceMember.user_id == user_id,
                SpaceMember.status == "active"
            ).first()
            return member is not None
        finally:
            session.close()

    def check_owner(self, user_id: str, space_id: str, db_factory) -> bool:
        """
        Check if a user is the owner of a space/team.

        Args:
            user_id: The user ID.
            space_id: The space/team ID.
            db_factory: Database session factory.

        Returns:
            True if user is the owner, False otherwise.
        """
        from .models import Space
        session = db_factory()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            return space is not None and space.owner_id == user_id
        finally:
            session.close()

    def get_team_count_for_pool(self, pool_id: str, db_factory) -> int:
        """
        Get the number of teams using a storage pool.

        Args:
            pool_id: The storage pool ID.
            db_factory: Database session factory.

        Returns:
            Number of teams using this pool.
        """
        from .models import Team
        session = db_factory()
        try:
            return session.query(Team).filter(Team.storage_pool_id == pool_id).count()
        finally:
            session.close()

    def get_member_count_for_space(self, space_id: str, db_factory) -> int:
        """
        Get the number of active members in a space.

        Args:
            space_id: The space ID.
            db_factory: Database session factory.

        Returns:
            Number of active members.
        """
        from .models import SpaceMember
        session = db_factory()
        try:
            return session.query(SpaceMember).filter(
                SpaceMember.space_id == space_id,
                SpaceMember.status == "active"
            ).count()
        finally:
            session.close()

    def get_available_pool_count(self, db_factory) -> int:
        """
        Get the number of available (active) storage pools.

        Args:
            db_factory: Database session factory.

        Returns:
            Number of available pools.
        """
        from .models import StoragePool
        session = db_factory()
        try:
            return session.query(StoragePool).filter(StoragePool.is_active == True).count()
        finally:
            session.close()