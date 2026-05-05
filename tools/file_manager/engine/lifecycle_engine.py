"""
Lifecycle constraint engine.

Provides declarative constraint checking with user guidance for violations.
Config source: config/lifecycle_config.yaml
"""

import logging
import os
from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

import yaml

from .lifecycle_exception import LifecycleViolation, GuidanceAction

# Configure logger for edge case logging
logger = logging.getLogger(__name__)

# Config file path (relative to file_manager root)
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "lifecycle_config.yaml")


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
    Config loaded from: config/lifecycle_config.yaml
    """

    def __init__(self, config_path: str = None):
        self._rules: Dict[str, ConstraintRule] = {}
        self._action_rules: Dict[str, List[ConstraintRule]] = {}
        self._config_path = config_path or _CONFIG_PATH
        self._load_config()

    def _load_config(self):
        """Load constraint rules from YAML config file."""
        if not os.path.exists(self._config_path):
            logger.warning(f"Config file not found: {self._config_path}, using hardcoded rules")
            self._init_default_rules()
            return

        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            lifecycle_cfg = config.get('lifecycle', {})
            self._enabled = lifecycle_cfg.get('enabled', True)
            self._debug = lifecycle_cfg.get('debug', False)

            rules = config.get('rules', {})
            for action, rule_list in rules.items():
                for rule_cfg in rule_list:
                    self._register_from_config(action, rule_cfg)

            logger.info(f"Loaded {len(self._rules)} lifecycle rules from {self._config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}, using hardcoded rules")
            self._init_default_rules()

    def _register_from_config(self, action: str, rule_cfg: Dict[str, Any]):
        """Register a rule from config dict."""
        code = rule_cfg['code']
        constraint_type_str = rule_cfg.get('constraint_type', 'pre_check')
        constraint_type = ConstraintType(constraint_type_str)

        # Map config field names to our internal names
        error_message = rule_cfg.get('error_template', rule_cfg.get('error_message', ''))
        guidance = rule_cfg.get('guidance', {})
        priority = rule_cfg.get('priority', 0)

        # Build check function based on context keys mentioned in description
        desc = rule_cfg.get('description', '').lower()
        check_fn = self._build_check_fn(code, desc)

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
        self.register_action_rule(action, code)

    def _build_check_fn(self, code: str, description: str) -> Callable:
        """Build check function based on rule code and description."""
        # Direct mapping from code to (context_key, check_type)
        # check_type: 'zero' = value should be 0 to pass, 'positive' = value should be > 0 to pass
        # 'bool' = truthy to pass, 'not_bool' = falsy to pass
        code_ctx_map = {
            'NOT_SPACE_OWNER': ('is_owner', 'bool'),
            'NOT_TEAM_OWNER': ('is_owner', 'bool'),
            'MEMBER_RECENTLY_REMOVED': ('was_recently_removed', 'not_bool'),
            'STORAGE_POOL_IN_USE': ('team_count', 'zero'),
            'POOL_TEAMS_MIGRATING': ('team_migrating_count', 'zero'),
            'SPACE_NO_MEMBERS': ('member_count', 'zero'),
            'SPACE_HAS_PENDING_REQUESTS': ('pending_request_count', 'zero'),
            'NO_AVAILABLE_POOL': ('available_pools', 'positive'),
            'CREDENTIAL_VALID': ('is_valid', 'bool'),
            'QUOTA_EXCEEDED': ('sufficient_quota', 'bool'),
        }

        # Special case: QUOTA_RESERVED can be overridden with can_override flag
        if code == 'QUOTA_RESERVED':
            return lambda ctx: ctx.get('quota_reserved', 0) == 0 or ctx.get('can_override', False)

        # Check direct code mapping first
        for prefix, (ctx_key, check_type) in code_ctx_map.items():
            if code.startswith(prefix) or prefix in code:
                if check_type == 'zero':
                    return lambda ctx, ck=ctx_key: ctx.get(ck, 0) == 0
                elif check_type == 'positive':
                    return lambda ctx, ck=ctx_key: ctx.get(ck, 0) > 0
                elif check_type == 'bool':
                    return lambda ctx, ck=ctx_key: ctx.get(ck, False)
                elif check_type == 'not_bool':
                    return lambda ctx, ck=ctx_key: not ctx.get(ck, False)

        # These context keys are used in the codebase - map to lambdas
        ctx_checks = {
            'is_member': lambda ctx: ctx.get('is_member', False),
            'sufficient_quota': lambda ctx: ctx.get('sufficient_quota', True),
            'quota_reserved': lambda ctx: ctx.get('quota_reserved', 0) == 0 or ctx.get('can_override', False),
            'available_pools': lambda ctx: ctx.get('available_pools', 0) > 0,
            'team_count': lambda ctx: ctx.get('team_count', 0) == 0,
            'team_migrating_count': lambda ctx: ctx.get('team_migrating_count', 0) == 0,
            'member_count': lambda ctx: ctx.get('member_count', 0) == 0,
            'pending_request_count': lambda ctx: ctx.get('pending_request_count', 0) == 0,
            'is_owner': lambda ctx: ctx.get('is_owner', False),
            'was_recently_removed': lambda ctx: not ctx.get('was_recently_removed', False),
            'is_valid': lambda ctx: ctx.get('is_valid', False) is not False,
            'is_team_member': lambda ctx: ctx.get('is_team_member', False),
        }

        for key, fn in ctx_checks.items():
            if key in description or key.replace('_', ' ') in description:
                return fn

        # Default: check for boolean truthiness of the code name in lowercase
        ctx_key = code.lower()
        if ctx_key in ['not_space_member', 'not_team_member']:
            return lambda ctx: ctx.get('is_member', False) or ctx.get('is_team_member', False)
        if ctx_key == 'quota_exceeded':
            return lambda ctx: ctx.get('sufficient_quota', True)

        return lambda ctx: True  # Default pass

    def _init_default_rules(self):
        """Initialize default constraint rules."""
        # delete_pool action
        self._register_default("STORAGE_POOL_IN_USE", ConstraintType.PRE_CHECK,
            lambda ctx: ctx.get("team_count", 0) == 0,
            "该存储池仍有团队使用，无法删除",
            {"label": "查看团队", "path": "/admin/teams"},
            action="delete_pool"
        )

        # Edge case: teams migrating
        self._register_default("POOL_TEAMS_MIGRATING", ConstraintType.STATE,
            lambda ctx: ctx.get("team_migrating_count", 0) == 0,
            "该存储池有团队正在迁移中",
            {"label": "查看迁移进度", "path": "/admin/teams?status=migrating"},
            action="delete_pool"
        )

        # upload_file action
        self._register_default("NOT_SPACE_MEMBER", ConstraintType.PRE_CHECK,
            lambda ctx: ctx.get("is_member", False),
            "请先加入团队或空间才能上传文件",
            {"label": "加入团队", "path": "/teams"},
            action="upload_file"
        )

        self._register_default("QUOTA_SUFFICIENT", ConstraintType.QUOTA,
            lambda ctx: ctx.get("sufficient_quota", True),
            "存储配额已用尽，无法上传新文件",
            {"label": "查看回收站", "path": "/trash"},
            action="upload_file"
        )

        # Edge case: concurrent upload quota reservation
        self._register_default("QUOTA_RESERVED", ConstraintType.QUOTA,
            lambda ctx: ctx.get("quota_reserved", 0) == 0 or ctx.get("can_override", False),
            "当前有文件正在上传，配额已被临时占用",
            {"label": "刷新状态", "action": "refreshQuota"},
            action="upload_file"
        )

        # create_team action
        self._register_default("NO_AVAILABLE_POOL", ConstraintType.PRE_CHECK,
            lambda ctx: ctx.get("available_pools", 0) > 0,
            "系统暂无可用存储池，请联系管理员创建",
            {"label": "联系管理员", "action": "contact_admin"},
            action="create_team"
        )

        # invite_member action
        self._register_default("NOT_SPACE_OWNER", ConstraintType.PERMISSION,
            lambda ctx: ctx.get("is_owner", False),
            "只有空间所有者可以邀请成员",
            {"label": "联系管理员", "action": "contact_admin"},
            action="invite_member"
        )

        # Edge case: recently removed member
        self._register_default("MEMBER_RECENTLY_REMOVED", ConstraintType.PRE_CHECK,
            lambda ctx: not ctx.get("was_recently_removed", False),
            "该成员刚被移除，请稍后再尝试邀请",
            {"label": "确定", "action": "dismiss"},
            action="invite_member"
        )

        # delete_team action
        self._register_default("NOT_TEAM_OWNER", ConstraintType.PERMISSION,
            lambda ctx: ctx.get("is_owner", False),
            "只有团队所有者可以删除团队",
            {"label": "联系管理员", "action": "contact_admin"},
            action="delete_team"
        )

        # join_team action (credential validation)
        self._register_default("CREDENTIAL_VALID", ConstraintType.PRE_CHECK,
            lambda ctx: ctx.get("is_valid", False) is not False,
            "邀请码已过期或无效",
            {"label": "返回", "path": "/teams"},
            action="join_team"
        )

        # delete_space action
        self._register_default("SPACE_NO_MEMBERS", ConstraintType.PRE_CHECK,
            lambda ctx: ctx.get("member_count", 0) == 0,
            "该空间仍有成员，无法删除",
            {"label": "查看成员", "path": "/space/members"},
            action="delete_space"
        )

        # Edge case: pending private space requests
        self._register_default("SPACE_HAS_PENDING_REQUESTS", ConstraintType.PRE_CHECK,
            lambda ctx: ctx.get("pending_request_count", 0) == 0,
            "该空间有待审核的私人空间申请",
            {"label": "查看申请", "path": "/space/requests"},
            action="delete_space"
        )

        # create_private_space action
        self._register_default("NOT_TEAM_MEMBER", ConstraintType.PRE_CHECK,
            lambda ctx: ctx.get("is_team_member", False),
            "只有团队成员才能申请私人空间",
            {"label": "加入团队", "path": "/teams"},
            action="create_private_space"
        )

        # check_quota action (pre-check before upload)
        self._register_default("QUOTA_EXCEEDED", ConstraintType.QUOTA,
            lambda ctx: ctx.get("sufficient_quota", True),
            "存储配额已用尽，无法上传新文件",
            {"label": "查看回收站", "path": "/trash"},
            action="check_quota"
        )

        # update_quota action (only owner can update)
        self._register_default("NOT_QUOTA_OWNER", ConstraintType.PERMISSION,
            lambda ctx: ctx.get("is_owner", False),
            "只有空间所有者可以修改配额",
            {"label": "联系管理员", "action": "contact_admin"},
            action="update_quota"
        )

    def _register_default(self, code: str, constraint_type: ConstraintType,
                          check_fn: Callable, error_message: str,
                          guidance: Dict[str, str], priority: int = 0,
                          action: Optional[str] = None):
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
        if action:
            self.register_action_rule(action, code)

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
                pass
        return None

    def raise_if_violated(self, action: str, context: Dict[str, Any]):
        """
        Check constraints and raise LifecycleViolation if any fail.
        Logs edge case violations for monitoring.
        """
        violated_rule = self.check(action, context)
        if violated_rule:
            guidance_config = violated_rule.guidance
            action_type = "navigate" if guidance_config.get("path") else "callback"

            # Log edge case violations for monitoring
            edge_case_codes = {"POOL_TEAMS_MIGRATING", "QUOTA_RESERVED",
                               "SPACE_HAS_PENDING_REQUESTS", "MEMBER_RECENTLY_REMOVED"}
            if violated_rule.code in edge_case_codes:
                logger.warning(
                    "Edge case lifecycle violation: action=%s, code=%s, context=%s",
                    action, violated_rule.code, context
                )

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
        """Check if a user is a member of a space/team."""
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
        """Check if a user is the owner of a space/team."""
        from .models import Space
        session = db_factory()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            return space is not None and space.owner_id == user_id
        finally:
            session.close()

    def get_team_count_for_pool(self, pool_id: str, db_factory) -> int:
        """Get the number of teams using a storage pool."""
        from .models import Team
        session = db_factory()
        try:
            return session.query(Team).filter(Team.storage_pool_id == pool_id).count()
        finally:
            session.close()

    def get_member_count_for_space(self, space_id: str, db_factory) -> int:
        """Get the number of active members in a space."""
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
        """Get the number of available (active) storage pools."""
        from .models import StoragePool
        session = db_factory()
        try:
            return session.query(StoragePool).filter(StoragePool.is_active == True).count()
        finally:
            session.close()

    def get_team_migrating_count(self, pool_id: str, db_factory) -> int:
        """
        Get the number of teams currently migrating from/to a storage pool.

        Edge case for delete_pool: teams being migrated cannot delete pool.
        """
        from .models import Team
        session = db_factory()
        try:
            return session.query(Team).filter(
                Team.storage_pool_id == pool_id,
                Team.status == "migrating"
            ).count()
        finally:
            session.close()

    def check_recently_removed_member(self, user_id: str, space_id: str,
                                       db_factory, hours: int = 24) -> bool:
        """
        Check if a member was recently removed from a space.

        Edge case for invite_member: recently removed members cannot be re-invited immediately.
        Returns True if member was removed within the specified hours.
        """
        from datetime import datetime, timedelta
        from .models import SpaceMember
        session = db_factory()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            member = session.query(SpaceMember).filter(
                SpaceMember.space_id == space_id,
                SpaceMember.user_id == user_id,
                SpaceMember.status == "removed",
                SpaceMember.updated_at >= cutoff
            ).first()
            return member is not None
        finally:
            session.close()

    def get_pending_request_count(self, space_id: str, db_factory) -> int:
        """
        Get the number of pending private space requests for a space.

        Edge case for delete_space: cannot delete space with pending requests.
        """
        from .models import SpaceRequest
        session = db_factory()
        try:
            return session.query(SpaceRequest).filter(
                SpaceRequest.space_id == space_id,
                SpaceRequest.status == "pending"
            ).count()
        finally:
            session.close()

    def get_quota_reserved(self, space_id: str, db_factory) -> int:
        """
        Get the amount of quota reserved by ongoing uploads.

        Edge case for upload_file: concurrent uploads temporarily reserve quota.
        Returns bytes reserved by incomplete uploads.
        """
        from .models import FileUpload
        session = db_factory()
        try:
            total = session.query(FileUpload.file_size).filter(
                FileUpload.space_id == space_id,
                FileUpload.status == "uploading"
            ).all()
            return sum(r[0] for r in total) if total else 0
        finally:
            session.close()


# =============================================================================
# Circuit Breaker for Lifecycle Engine
# =============================================================================

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject all requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5      # failures before opening
    success_threshold: int = 2     # successes in half-open to close
    timeout_seconds: float = 30.0  # time before trying half-open
    half_open_max_calls: int = 3   # max calls in half-open state


@dataclass
class CircuitBreaker:
    """
    Circuit breaker to protect lifecycle engine from cascading failures.

    When a constraint check fails repeatedly (e.g., database timeout),
    the circuit opens and quickly rejects subsequent requests to avoid
    resource exhaustion. After a timeout period, it enters half-open state
    and allows a limited number of test requests.
    """
    name: str
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _last_failure_time: Optional[datetime] = field(default=None, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _half_open_calls: int = field(default=0, init=False)

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if timeout expired
                if self._last_failure_time:
                    elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
                    if elapsed >= self.config.timeout_seconds:
                        logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN after {elapsed:.1f}s timeout")
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_calls = 0
            return self._state

    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    logger.info(f"Circuit breaker '{self.name}' closing after {self._success_count} successes")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open opens the circuit again
                logger.warning(f"Circuit breaker '{self.name}' opening from HALF_OPEN after failure")
                self._state = CircuitState.OPEN
                self._half_open_calls = 0
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    logger.warning(f"Circuit breaker '{self.name}' opening after {self._failure_count} failures")
                    self._state = CircuitState.OPEN

    def can_execute(self) -> bool:
        """Check if a request can be executed."""
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.OPEN:
            return False
        if state == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for monitoring."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
            }


class LifecycleCircuitBreaker:
    """
    Circuit breaker manager for lifecycle constraint checks.

    Provides per-action circuit breakers to isolate failures
    and prevent cascading degradation.
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._default_config = config or CircuitBreakerConfig()
        self._lock = threading.Lock()

    def get_breaker(self, action: str) -> CircuitBreaker:
        """Get or create circuit breaker for an action."""
        with self._lock:
            if action not in self._breakers:
                self._breakers[action] = CircuitBreaker(
                    name=f"lifecycle_{action}",
                    config=self._default_config,
                )
            return self._breakers[action]

    def execute(self, action: str, fn: Callable, *args, **kwargs):
        """
        Execute a function with circuit breaker protection.

        Raises:
            CircuitBreakerOpen: When the circuit is open
        """
        breaker = self.get_breaker(action)

        if not breaker.can_execute():
            raise CircuitBreakerOpen(f"Circuit breaker open for action '{action}'")

        try:
            result = fn(*args, **kwargs)
            breaker.record_success()
            return result
        except Exception as e:
            breaker.record_failure()
            raise

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers."""
        with self._lock:
            return {name: b.get_status() for name, b in self._breakers.items()}

    def reset_all(self) -> None:
        """Reset all circuit breakers to closed state."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker._state = CircuitState.CLOSED
                breaker._failure_count = 0
                breaker._success_count = 0


class CircuitBreakerOpen(Exception):
    """Raised when a circuit breaker is open."""
    pass