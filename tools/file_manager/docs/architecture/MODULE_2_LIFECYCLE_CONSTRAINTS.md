# 模块二：生命周期操作约束 - 详细设计

## 1. 技术架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (Web/Tauri)                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              LifecycleInterceptor                        │   │
│  │  - beforeAction(action, context)                        │   │
│  │  - showGuidanceModal(config)                            │   │
│  │  - executeGuidance(action)                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                     ┌──────────▼──────────┐
                     │   Error Response    │
                     │   (LifecycleViolation)│
                     └──────────┬──────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                        Backend (Python)                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 LifecycleEngine                         │   │
│  │  - @lifecycle_constraint decorator                      │   │
│  │  - ConstraintRule registry                              │   │
│  │  - check_and_raise(context)                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌───────────────────────────▼─────────────────────────────┐   │
│  │                   Services Layer                        │   │
│  │  TeamService │ SpaceService │ FileService              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 约束分类

| 类别 | 说明 | 示例 |
|------|------|------|
| 前置条件约束 | 操作前必须满足的条件 | 必须是成员才能上传 |
| 独占性约束 | 同时只能有一个操作 | 删除存储池时不能有团队使用 |
| 状态约束 | 资源必须在特定状态 | 存储池必须 active |
| 配额约束 | 不能超过资源限制 | 配额不足不能写入 |
| 权限约束 | 必须有特定权限 | 只有 Owner 才能邀请成员 |

---

## 2. 后端约束引擎

### 2.1 核心异常定义

```python
# engine/lifecycle_exception.py

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum

class ErrorCode(Enum):
    """生命周期错误码"""
    # 存储池相关
    POOL_NOT_FOUND = "POOL_NOT_FOUND"
    POOL_IN_USE = "STORAGE_POOL_IN_USE"
    POOL_INACTIVE = "STORAGE_POOL_INACTIVE"
    NO_AVAILABLE_POOL = "NO_AVAILABLE_POOL"

    # 空间相关
    SPACE_NOT_FOUND = "SPACE_NOT_FOUND"
    SPACE_HAS_MEMBERS = "SPACE_HAS_MEMBERS"
    NOT_SPACE_OWNER = "NOT_SPACE_OWNER"
    NOT_SPACE_MEMBER = "NOT_SPACE_MEMBER"

    # 团队相关
    TEAM_NOT_FOUND = "TEAM_NOT_FOUND"
    NOT_TEAM_OWNER = "NOT_TEAM_OWNER"
    MEMBER_LIMIT_EXCEEDED = "MEMBER_LIMIT_EXCEEDED"

    # 配额相关
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    TEAM_QUOTA_EXCEEDED = "TEAM_QUOTA_EXCEEDED"
    POOL_QUOTA_EXCEEDED = "POOL_QUOTA_EXCEEDED"

    # 凭证相关
    INVALID_CREDENTIAL = "INVALID_CREDENTIAL"
    CREDENTIAL_EXPIRED = "CREDENTIAL_EXPIRED"
    CREDENTIAL_USED_UP = "CREDENTIAL_USED_UP"

    # 通用
    LIFECYCLE_VIOLATION = "LIFECYCLE_VIOLATION"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"


@dataclass
class GuidanceAction:
    """引导操作配置"""
    label: str                           # 按钮文本
    icon: str = ""                       # 图标 emoji
    action_type: str = "navigate"        # navigate | callback | modal
    path: Optional[str] = None          # 跳转路径
    callback: Optional[str] = None       # 回调函数名
    modal_config: Optional[Dict] = None  # 弹窗配置


@dataclass
class LifecycleViolation(Exception):
    """
    生命周期约束违反异常

    当操作违反生命周期规则时抛出此异常。
    包含用户友好的错误信息和引导操作。
    """
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    guidance: Optional[GuidanceAction] = None
    http_status: int = 403

    def __post_init__(self):
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为 API 响应格式"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "guidance": {
                    "label": self.guidance.label if self.guidance else None,
                    "icon": self.guidance.icon if self.guidance else None,
                    "action_type": self.guidance.action_type if self.guidance else None,
                    "path": self.guidance.path if self.guidance else None
                }
            }
        }

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
        return cls(
            code=ErrorCode.QUOTA_EXCEEDED.value,
            message=f"空间「{space_name}」配额已用尽（{used/max*100:.0f}%），无法上传新文件。请清理回收站或联系管理员申请扩容。",
            details={"space_name": space_name, "used_bytes": used, "max_bytes": max, "required_bytes": required},
            guidance=GuidanceAction(
                label="查看回收站",
                icon="🗑️",
                action_type="navigate",
                path="/trash"
            )
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
```

### 2.2 约束规则定义

```python
# engine/lifecycle_engine.py

from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import functools

class ConstraintType(Enum):
    """约束类型"""
    PRE_CHECK = "pre_check"           # 前置条件检查
    MUTEX = "mutex"                  # 互斥检查
    STATE = "state"                  # 状态检查
    QUOTA = "quota"                  # 配额检查
    PERMISSION = "permission"         # 权限检查


@dataclass
class ConstraintRule:
    """约束规则定义"""
    code: str                          # 错误码
    name: str                          # 规则名称
    constraint_type: ConstraintType    # 约束类型
    check_fn: Callable[[Any], bool]    # 检查函数
    error_message: str                 # 错误消息
    guidance: Dict[str, str]           # 引导操作
    priority: int = 0                  # 优先级


class LifecycleEngine:
    """生命周期约束引擎"""

    def __init__(self):
        self._rules: Dict[str, ConstraintRule] = {}
        self._action_rules: Dict[str, List[ConstraintRule]] = {}
        self._init_default_rules()

    def _init_default_rules(self):
        """初始化默认约束规则"""

        # 存储池删除约束
        self.register_rule(ConstraintRule(
            code="STORAGE_POOL_IN_USE",
            name="存储池使用中",
            constraint_type=ConstraintType.PRE_CHECK,
            check_fn=lambda ctx: ctx.get("team_count", 0) == 0,
            error_message="该存储池仍有团队使用，无法删除",
            guidance={"label": "查看团队", "path": "/admin/teams"}
        ))

        # 上传文件约束
        self.register_rule(ConstraintRule(
            code="NOT_SPACE_MEMBER",
            name="非空间成员",
            constraint_type=ConstraintType.PRE_CHECK,
            check_fn=lambda ctx: ctx.get("is_member", False),
            error_message="请先加入团队或空间才能上传文件",
            guidance={"label": "加入团队", "path": "/teams"}
        ))

        # 团队创建约束
        self.register_rule(ConstraintRule(
            code="NO_AVAILABLE_POOL",
            name="无可用存储池",
            constraint_type=ConstraintType.PRE_CHECK,
            check_fn=lambda ctx: ctx.get("available_pools", 0) > 0,
            error_message="系统暂无可用存储池，请联系管理员创建",
            guidance={"label": "联系管理员", "action": "contact_admin"}
        ))

        # 配额检查约束
        self.register_rule(ConstraintRule(
            code="QUOTA_EXCEEDED",
            name="配额超限",
            constraint_type=ConstraintType.QUOTA,
            check_fn=lambda ctx: ctx.get("sufficient_quota", False),
            error_message="存储配额已用尽，无法上传新文件",
            guidance={"label": "查看回收站", "path": "/trash"}
        ))

        # 邀请成员约束
        self.register_rule(ConstraintRule(
            code="NOT_SPACE_OWNER",
            name="非空间所有者",
            constraint_type=ConstraintType.PERMISSION,
            check_fn=lambda ctx: ctx.get("is_owner", False),
            error_message="只有空间所有者可以邀请成员",
            guidance={"label": "联系管理员", "action": "contact_admin"}
        ))

    def register_rule(self, rule: ConstraintRule):
        """注册约束规则"""
        self._rules[rule.code] = rule

    def register_action_rule(self, action: str, rule_code: str):
        """将规则关联到特定操作"""
        if action not in self._action_rules:
            self._action_rules[action] = []
        if rule_code in self._rules:
            self._action_rules[action].append(self._rules[rule_code])

    def check(self, action: str, context: Dict[str, Any]) -> ConstraintRule:
        """
        检查操作是否允许

        Returns:
            None 如果检查通过
            ConstraintRule 如果检查失败
        """
        rules = self._action_rules.get(action, [])
        for rule in sorted(rules, key=lambda r: r.priority):
            if not rule.check_fn(context):
                return rule
        return None

    def raise_if_violated(self, action: str, context: Dict[str, Any]):
        """检查约束，不通过则抛出异常"""
        violated_rule = self.check(action, context)
        if violated_rule:
            raise LifecycleViolation(
                code=violated_rule.code,
                message=violated_rule.error_message,
                guidance=GuidanceAction(
                    label=violated_rule.guidance.get("label", "确定"),
                    path=violated_rule.guidance.get("path"),
                    action_type="navigate" if violated_rule.guidance.get("path") else "callback"
                )
            )
```

### 2.3 约束装饰器

```python
# engine/lifecycle_decorators.py

from functools import wraps
from typing import Callable, Dict, Any

def lifecycle_constraint(
    action: str,
    context_builder: Callable[..., Dict[str, Any]]
):
    """
    生命周期约束装饰器

    用法:
    @lifecycle_constraint(
        action="delete_pool",
        context_builder=lambda pool_id: build_delete_pool_context(pool_id)
    )
    async def delete_pool(pool_id: str):
        ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 构建上下文
            context = context_builder(*args, **kwargs)
            # 检查约束
            engine = get_lifecycle_engine()
            engine.raise_if_violated(action, context)
            # 执行原操作
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = context_builder(*args, **kwargs)
            engine = get_lifecycle_engine()
            engine.raise_if_violated(action, context)
            return func(*args, **kwargs)

        # 根据函数类型选择装饰器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def pre_check(check_fn: Callable[[Any], bool], error: LifecycleViolation):
    """
    前置条件检查装饰器

    用法:
    @pre_check(
        check_fn=lambda ctx: ctx["is_member"],
        error=LifecycleViolation.not_space_member()
    )
    async def upload_file(...):
        ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not check_fn(kwargs):
                raise error
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not check_fn(kwargs):
                raise error
            return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
```

### 2.4 服务层约束集成

```python
# services/team_service.py

class TeamService:
    """团队服务 - 集成生命周期约束"""

    def __init__(self, db_factory, lifecycle_engine: LifecycleEngine = None):
        self._db = db_factory
        self._lifecycle = lifecycle_engine or get_lifecycle_engine()

    def delete_pool(self, pool_id: str, requesting_user_id: str) -> None:
        """
        删除存储池

        约束: 存储池不能有任何团队使用
        """
        session = self._db()
        try:
            pool = session.query(StoragePool).filter(StoragePool.id == pool_id).first()
            if not pool:
                raise StoragePoolNotFound(f"存储池 {pool_id} 不存在")

            # 检查约束: 是否有团队使用
            teams = session.query(Team).filter(Team.storage_pool_id == pool_id).all()
            team_count = len(teams)

            context = {
                "pool_id": pool_id,
                "team_count": team_count,
                "requesting_user_id": requesting_user_id
            }

            # 使用约束引擎检查
            self._lifecycle.raise_if_violated("delete_pool", context)

            # 约束通过，执行删除
            session.delete(pool)
            session.commit()

        finally:
            session.close()

    def create_team(
        self,
        name: str,
        owner_id: str,
        storage_pool_id: str,
        max_bytes: int = 0,
    ) -> Dict[str, Any]:
        """
        创建团队

        约束: 必须有可用的存储池
        """
        session = self._db()
        try:
            # 约束检查: 是否有可用存储池
            pools = session.query(StoragePool).filter(StoragePool.is_active == True).all()

            context = {
                "available_pools": len(pools),
                "owner_id": owner_id
            }

            self._lifecycle.raise_if_violated("create_team", context)

            # 继续原有逻辑...
            # ...

        finally:
            session.close()
```

```python
# services/space_service.py

class SpaceService:
    """空间服务 - 集成生命周期约束"""

    def __init__(self, db_factory, lifecycle_engine: LifecycleEngine = None):
        self._db = db_factory
        self._lifecycle = lifecycle_engine or get_lifecycle_engine()

    async def upload_file(
        self,
        user_id: str,
        space_id: str,
        file_data: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        上传文件

        约束:
        - 用户必须是空间成员
        - 空间配额必须足够
        """
        session = self._db()
        try:
            # 约束检查: 是否是成员
            membership = session.query(SpaceMember).filter(
                SpaceMember.space_id == space_id,
                SpaceMember.user_id == user_id
            ).first()

            context = {
                "user_id": user_id,
                "space_id": space_id,
                "is_member": membership is not None,
                "file_size": len(file_data)
            }

            self._lifecycle.raise_if_violated("upload_file", context)

            # 检查配额
            space = session.query(Space).filter(Space.id == space_id).first()
            if space.max_bytes > 0:
                if space.used_bytes + len(file_data) > space.max_bytes:
                    raise LifecycleViolation.quota_exceeded(
                        space_name=space.name,
                        used=space.used_bytes,
                        max=space.max_bytes,
                        required=len(file_data)
                    )

            # 执行上传...
            # ...

        finally:
            session.close()

    def invite_member(
        self,
        space_id: str,
        inviter_id: str,
        target_user_id: str,
        role: str = "member"
    ) -> SpaceCredential:
        """
        邀请成员

        约束: 只有空间所有者可以邀请
        """
        session = self._db()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound()

            context = {
                "space_id": space_id,
                "inviter_id": inviter_id,
                "is_owner": space.owner_id == inviter_id
            }

            self._lifecycle.raise_if_violated("invite_member", context)

            # 执行邀请逻辑...
            # ...

        finally:
            session.close()
```

### 2.5 FastAPI 错误处理

```python
# api/lifecycle_handler.py

from fastapi import Request, status
from fastapi.responses import JSONResponse

async def lifecycle_violation_handler(request: Request, exc: LifecycleViolation) -> JSONResponse:
    """生命周期违规异常处理器"""

    # 记录日志
    logger.warning(
        "Lifecycle violation: code=%s, message=%s, path=%s",
        exc.code, exc.message, request.url.path
    )

    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict()
    )


# 在 main.py 中注册
from fastapi import FastAPI

app = FastAPI()

app.add_exception_handler(LifecycleViolation, lifecycle_violation_handler)
```

---

## 3. 前端约束拦截器

### 3.1 核心类实现

```javascript
// web/js/lifecycle-interceptor.js

/**
 * 生命周期操作拦截器
 *
 * 在执行危险操作前检查约束条件，
 * 违规时显示引导弹窗而非直接拒绝
 */
class LifecycleInterceptor {
    constructor(options = {}) {
        this.enabled = options.enabled ?? true
        this.debug = options.debug ?? false
        this.constraints = new Map()
        this.guidanceCallbacks = new Map()

        this.init()
    }

    init() {
        this.registerDefaultConstraints()
        this.setupGlobalHandlers()
    }

    registerDefaultConstraints() {
        // 上传文件约束
        this.registerConstraint('upload_file', {
            check: async (context) => {
                return context.isMember && context.hasQuota
            },
            error: {
                title: '无法上传文件',
                message: '您还没有加入任何团队，无法上传文件。请先加入一个团队或创建一个新团队。',
                icon: '📤'
            },
            guidance: {
                label: '加入团队',
                icon: '👥',
                path: '/teams'
            }
        })

        // 创建团队约束
        this.registerConstraint('create_team', {
            check: async (context) => {
                return context.hasAvailablePool
            },
            error: {
                title: '无法创建团队',
                message: '系统暂无可用存储池，无法创建新团队。请联系管理员创建存储池后再试。',
                icon: '👥'
            },
            guidance: {
                label: '联系管理员',
                icon: '📧',
                action: 'showContactAdminModal'
            }
        })

        // 删除存储池约束
        this.registerConstraint('delete_pool', {
            check: async (context) => {
                return context.teamCount === 0
            },
            error: {
                title: '无法删除存储池',
                message: '该存储池仍有团队使用，无法删除。请先将团队迁移到其他存储池。',
                icon: '⚠️'
            },
            guidance: {
                label: '查看团队',
                icon: '👥',
                path: '/admin/teams'
            }
        })

        // 邀请成员约束
        this.registerConstraint('invite_member', {
            check: async (context) => {
                return context.isOwner
            },
            error: {
                title: '无法邀请成员',
                message: '只有团队所有者可以邀请新成员。',
                icon: '👥'
            },
            guidance: {
                label: '联系管理员',
                icon: '📧',
                action: 'showContactAdminModal'
            }
        })

        // 配额检查约束
        this.registerConstraint('check_quota', {
            check: async (context) => {
                return context.sufficientQuota
            },
            error: {
                title: '配额不足',
                message: '存储配额已用尽，无法上传新文件。请清理回收站或联系管理员申请扩容。',
                icon: '💾'
            },
            guidance: {
                label: '查看回收站',
                icon: '🗑️',
                path: '/trash'
            }
        })
    }

    /**
     * 注册约束规则
     */
    registerConstraint(action, config) {
        this.constraints.set(action, config)
    }

    /**
     * 注册引导回调
     */
    registerGuidanceCallback(action, callback) {
        this.guidanceCallbacks.set(action, callback)
    }

    /**
     * 执行操作前的约束检查
     */
    async beforeAction(action, context) {
        if (!this.enabled) return { allowed: true }

        const constraint = this.constraints.get(action)
        if (!constraint) {
            this.debug && console.log(`[Lifecycle] No constraint for action: ${action}`)
            return { allowed: true }
        }

        try {
            const passed = await constraint.check(context)

            if (passed) {
                this.debug && console.log(`[Lifecycle] Constraint passed: ${action}`)
                return { allowed: true }
            }

            // 约束违反，显示引导弹窗
            this.debug && console.log(`[Lifecycle] Constraint violated: ${action}`)
            return {
                allowed: false,
                error: constraint.error,
                guidance: constraint.guidance
            }

        } catch (e) {
            console.error(`[Lifecycle] Error checking constraint: ${action}`, e)
            return { allowed: true, error: e.message }
        }
    }

    /**
     * 显示引导弹窗
     */
    showGuidanceModal(config) {
        const modal = new GuidanceModal({
            title: config.error.title,
            message: config.error.message,
            icon: config.error.icon,
            guidance: config.guidance,
            onAction: () => this.executeGuidance(config.guidance),
            onDismiss: () => this.onGuidanceDismissed(config)
        })
        modal.show()
        return modal
    }

    /**
     * 执行引导操作
     */
    executeGuidance(guidance) {
        if (guidance.path) {
            // 导航到指定路径
            router.push(guidance.path)
        } else if (guidance.action) {
            // 执行回调
            const callback = this.guidanceCallbacks.get(guidance.action)
            if (callback) {
                callback()
            }
        }
    }

    /**
     * 引导弹窗关闭后的处理
     */
    onGuidanceDismissed(config) {
        // 可选：记录用户已忽略此引导
        localStorage.setItem(`guidance_dismissed_${config.action}`, Date.now().toString())
    }

    /**
     * 设置全局错误处理
     */
    setupGlobalHandlers() {
        // 拦截 API 错误响应
        window.addEventListener('unhandledrejection', (event) => {
            if (event.reason?.code?.startsWith('LIFECYCLE_')) {
                event.preventDefault()
                this.handleApiError(event.reason)
            }
        })
    }

    /**
     * 处理 API 错误
     */
    handleApiError(error) {
        if (error.guidance) {
            this.showGuidanceModal({
                error: { title: error.message, message: error.details?.message || error.message },
                guidance: error.guidance
            })
        }
    }
}

// 创建全局单例
window.lifecycleInterceptor = new LifecycleInterceptor({ debug: false })
```

### 3.2 引导弹窗组件

```javascript
// web/js/components/GuidanceModal.js

/**
 * 引导弹窗组件
 *
 * 用于显示生命周期约束违反时的用户引导
 */
class GuidanceModal {
    constructor(options = {}) {
        this.title = options.title || '操作受限'
        this.message = options.message || ''
        this.icon = options.icon || '⚠️'
        this.guidance = options.guidance || {}
        this.onAction = options.onAction || (() => {})
        this.onDismiss = options.onDismiss || (() => {})
        this.modalId = 'guidance-modal-' + Date.now()
    }

    show() {
        // 创建模态框
        const modalHtml = `
            <div class="guidance-modal" id="${this.modalId}">
                <div class="guidance-overlay"></div>
                <div class="guidance-dialog">
                    <div class="guidance-header">
                        <span class="guidance-icon">${this.icon}</span>
                        <h3 class="guidance-title">${this.escapeHtml(this.title)}</h3>
                        <button class="guidance-close" aria-label="关闭">×</button>
                    </div>
                    <div class="guidance-body">
                        <p class="guidance-message">${this.escapeHtml(this.message)}</p>
                        <div class="guidance-details" style="display:none;"></div>
                    </div>
                    <div class="guidance-footer">
                        <button class="guidance-action primary">
                            ${this.guidance.icon ? `<span class="action-icon">${this.guidance.icon}</span>` : ''}
                            <span class="action-label">${this.guidance.label || '确定'}</span>
                        </button>
                        <button class="guidance-dismiss">
                            取消
                        </button>
                    </div>
                </div>
            </div>
        `

        // 插入到 body
        document.body.insertAdjacentHTML('beforeend', modalHtml)

        // 绑定事件
        this.bindEvents()

        // 显示动画
        requestAnimationFrame(() => {
            document.getElementById(this.modalId).classList.add('show')
        })
    }

    bindEvents() {
        const modal = document.getElementById(this.modalId)
        const overlay = modal.querySelector('.guidance-overlay')
        const closeBtn = modal.querySelector('.guidance-close')
        const actionBtn = modal.querySelector('.guidance-action')
        const dismissBtn = modal.querySelector('.guidance-dismiss')

        overlay.addEventListener('click', () => this.hide())
        closeBtn.addEventListener('click', () => this.hide())
        dismissBtn.addEventListener('click', () => this.hide())
        actionBtn.addEventListener('click', () => {
            this.hide()
            this.onAction()
        })

        // ESC 键关闭
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && document.getElementById(this.modalId)) {
                this.hide()
            }
        })
    }

    hide() {
        const modal = document.getElementById(this.modalId)
        if (modal) {
            modal.classList.remove('show')
            setTimeout(() => {
                modal.remove()
                this.onDismiss()
            }, 200)
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div')
        div.textContent = text
        return div.innerHTML
    }
}
```

### 3.3 CSS 样式

```css
/* web/css/guidance-modal.css */

.guidance-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.2s ease;
}

.guidance-modal.show {
    opacity: 1;
}

.guidance-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.6);
}

.guidance-dialog {
    position: relative;
    background: var(--bg-secondary, #1a1f26);
    border: 1px solid var(--border, #30363d);
    border-radius: 12px;
    max-width: 420px;
    width: 90%;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    transform: scale(0.95);
    transition: transform 0.2s ease;
}

.guidance-modal.show .guidance-dialog {
    transform: scale(1);
}

.guidance-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border, #30363d);
}

.guidance-icon {
    font-size: 24px;
}

.guidance-title {
    flex: 1;
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary, #e6edf3);
}

.guidance-close {
    background: none;
    border: none;
    font-size: 20px;
    color: var(--text-secondary, #8b949e);
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition: background 0.15s;
}

.guidance-close:hover {
    background: rgba(255, 255, 255, 0.1);
}

.guidance-body {
    padding: 20px;
}

.guidance-message {
    margin: 0;
    font-size: 14px;
    line-height: 1.6;
    color: var(--text-secondary, #8b949e);
}

.guidance-footer {
    display: flex;
    gap: 12px;
    padding: 16px 20px;
    border-top: 1px solid var(--border, #30363d);
}

.guidance-action {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px 16px;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
}

.guidance-action.primary {
    background: var(--primary-color, #238636);
    color: white;
}

.guidance-action.primary:hover {
    background: var(--primary-hover, #2ea043);
}

.guidance-dismiss {
    padding: 10px 16px;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 6px;
    color: var(--text-primary, #e6edf3);
    font-size: 14px;
    cursor: pointer;
}

.guidance-dismiss:hover {
    background: rgba(255, 255, 255, 0.15);
}

.action-icon {
    font-size: 16px;
}
```

### 3.4 使用示例

```html
<!-- 在 HTML 中使用 -->
<button id="uploadBtn" onclick="handleUpload()">上传文件</button>

<script>
async function handleUpload() {
    const context = {
        isMember: await checkMembership(userId, spaceId),
        hasQuota: await checkQuota(spaceId, fileSize)
    }

    // 使用拦截器检查
    const result = await lifecycleInterceptor.beforeAction('upload_file', context)

    if (!result.allowed) {
        // 显示引导弹窗
        lifecycleInterceptor.showGuidanceModal(result)
        return
    }

    // 继续上传
    await uploadFile(...)
}
</script>
```

```javascript
// 注册引导回调
lifecycleInterceptor.registerGuidanceCallback('showContactAdminModal', () => {
    showContactAdminDialog({
        title: '联系管理员',
        message: '请联系系统管理员创建存储池或解决此问题。',
        adminEmail: 'admin@example.com'
    })
})
```

---

## 4. 约束规则表

| 操作 | 约束代码 | 检查条件 | 错误提示 | 引导操作 |
|------|---------|---------|---------|---------|
| upload_file | NOT_SPACE_MEMBER | 是 Space 成员 | "请先加入团队或空间才能上传文件" | 加入团队 |
| upload_file | QUOTA_EXCEEDED | 配额足够 | "存储配额已用尽，无法上传新文件" | 查看回收站 |
| create_team | NO_AVAILABLE_POOL | 有可用存储池 | "系统暂无可用存储池，无法创建新团队" | 联系管理员 |
| create_private_space | NOT_TEAM_MEMBER | 是团队成员 | "只有团队成员才能申请私人空间" | 加入团队 |
| delete_pool | STORAGE_POOL_IN_USE | 无团队使用 | "该存储池仍有团队使用，无法删除" | 查看团队 |
| delete_space | SPACE_HAS_MEMBERS | 无活跃成员 | "该空间仍有成员，无法删除" | 移除成员 |
| invite_member | NOT_SPACE_OWNER | 是 Space Owner | "只有空间所有者可以邀请成员" | 联系管理员 |
| delete_team | NOT_TEAM_OWNER | 是 Team Owner | "只有团队所有者可以删除团队" | 联系管理员 |
| update_quota | NOT_SPACE_OWNER | 是 Space Owner | "只有空间所有者可以修改配额" | 联系管理员 |
| join_team | VALID_CREDENTIAL | 凭证有效 | "邀请码已过期或无效" | 联系管理员 |

---

## 5. 测试策略

### 5.1 单元测试

```python
# tests/test_lifecycle_engine.py

import pytest

class TestLifecycleEngine:
    """生命周期引擎单元测试"""

    def test_register_rule(self, engine):
        rule = ConstraintRule(
            code="TEST_RULE",
            name="测试规则",
            constraint_type=ConstraintType.PRE_CHECK,
            check_fn=lambda ctx: ctx.get("value", 0) > 0,
            error_message="测试失败",
            guidance={"label": "测试", "path": "/test"}
        )

        engine.register_rule(rule)
        assert "TEST_RULE" in engine._rules

    def test_check_pass(self, engine):
        context = {"value": 10, "is_member": True}
        result = engine.check("upload_file", context)
        assert result is None  # None means pass

    def test_check_fail(self, engine):
        context = {"value": 0, "is_member": False}
        result = engine.check("upload_file", context)
        assert result is not None
        assert result.code == "NOT_SPACE_MEMBER"

    def test_raise_if_violated(self, engine):
        context = {"value": 0, "is_member": False}
        with pytest.raises(LifecycleViolation) as exc:
            engine.raise_if_violated("upload_file", context)

        assert exc.value.code == "NOT_SPACE_MEMBER"
        assert exc.value.guidance.label == "加入团队"


class TestLifecycleViolation:
    """生命周期异常单元测试"""

    def test_not_space_member(self):
        error = LifecycleViolation.not_space_member("user-1", "space-1")

        assert error.code == "NOT_SPACE_MEMBER"
        assert "团队" in error.message
        assert error.guidance.path == "/teams"

    def test_pool_in_use(self):
        teams = [
            {"id": "t1", "name": "Team-A"},
            {"id": "t2", "name": "Team-B"}
        ]
        error = LifecycleViolation.pool_in_use("pool-1", teams)

        assert error.code == "STORAGE_POOL_IN_USE"
        assert "Team-A" in error.message
        assert "Team-B" in error.message
        assert error.http_status == 409

    def test_quota_exceeded(self):
        error = LifecycleViolation.quota_exceeded(
            space_name="项目A",
            used=95 * 1024 * 1024 * 1024,
            max=100 * 1024 * 1024 * 1024,
            required=10 * 1024 * 1024 * 1024
        )

        assert error.code == "QUOTA_EXCEEDED"
        assert "95%" in error.message
        assert error.guidance.path == "/trash"

    def test_to_dict(self):
        error = LifecycleViolation.not_team_owner()
        data = error.to_dict()

        assert "error" in data
        assert data["error"]["code"] == "NOT_TEAM_OWNER"
        assert "guidance" in data["error"]
```

### 5.2 集成测试

```python
# tests/test_lifecycle_integration.py

import pytest
from fastapi.testclient import TestClient

class TestTeamServiceConstraints:
    """团队服务约束集成测试"""

    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)

    def test_delete_pool_with_teams_fails(self, client, auth_headers, sample_pool_with_team):
        """删除有团队使用的存储池应失败"""
        response = client.delete(
            f"/api/v1/pools/{sample_pool_with_team['pool_id']}",
            headers=auth_headers
        )

        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "STORAGE_POOL_IN_USE"
        assert "guidance" in data["error"]

    def test_delete_pool_without_teams_succeeds(self, client, auth_headers, empty_pool):
        """删除无团队使用的存储池应成功"""
        response = client.delete(
            f"/api/v1/pools/{empty_pool['id']}",
            headers=auth_headers
        )

        assert response.status_code == 200

    def test_create_team_without_pool_fails(self, client, auth_headers):
        """无可用存储池时创建团队应失败"""
        response = client.post(
            "/api/v1/teams",
            headers=auth_headers,
            json={
                "name": "New Team",
                "storage_pool_id": "non-existent-pool"
            }
        )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "NO_AVAILABLE_POOL"
```

### 5.3 前端测试

```javascript
// tests/unit/lifecycle-interceptor.spec.js

describe('LifecycleInterceptor', () => {
    let interceptor

    beforeEach(() => {
        interceptor = new LifecycleInterceptor({ debug: true })
    })

    describe('beforeAction', () => {
        it('allows action when constraint passes', async () => {
            const context = { isMember: true, hasQuota: true }
            const result = await interceptor.beforeAction('upload_file', context)

            expect(result.allowed).toBe(true)
        })

        it('blocks action when constraint fails', async () => {
            const context = { isMember: false, hasQuota: false }
            const result = await interceptor.beforeAction('upload_file', context)

            expect(result.allowed).toBe(false)
            expect(result.error).toBeDefined()
            expect(result.guidance).toBeDefined()
        })

        it('shows guidance modal when blocked', async () => {
            const context = { isMember: false }
            const showModalSpy = jest.spyOn(interceptor, 'showGuidanceModal')

            await interceptor.beforeAction('upload_file', context)

            expect(showModalSpy).toHaveBeenCalled()
        })
    })

    describe('registerConstraint', () => {
        it('registers new constraint', () => {
            interceptor.registerConstraint('custom_action', {
                check: (ctx) => ctx.value > 0,
                error: { title: 'Test', message: 'Test error' },
                guidance: { label: 'Test' }
            })

            expect(interceptor.constraints.has('custom_action')).toBe(true)
        })
    })
})
```

---

## 6. 部署配置

### 6.1 环境变量

```bash
# .env
LIFECYCLE_ENABLED=true
LIFECYCLE_DEBUG=false
LIFECYCLE_CACHE_TTL=300
```

### 6.2 约束规则配置

```yaml
# config/lifecycle_rules.yaml
rules:
  upload_file:
    - code: NOT_SPACE_MEMBER
      check: membership_check
      error_template: "请先加入团队或空间才能上传文件"
      guidance:
        label: "加入团队"
        path: "/teams"

  delete_pool:
    - code: STORAGE_POOL_IN_USE
      check: team_count_zero
      error_template: "该存储池仍有 {team_count} 个团队使用"
      guidance:
        label: "查看团队"
        path: "/admin/teams"
```