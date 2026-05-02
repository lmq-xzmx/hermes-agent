# 生命周期操作约束实现

## 领域分类

**领域**：企业级文件管理 / 云存储协作平台 (Enterprise File Management & Cloud Storage Collaboration Platform)

**子领域**：
- 多租户存储资源管理 (Multi-tenant Storage Resource Management)
- 基于角色的访问控制 (RBAC - Role-Based Access Control)
- 操作约束与数据一致性保护 (Operation Constraints & Data Consistency)

---

## 约束规则设计

### 规则定义

```python
# 生命周期约束规则
LIFECYCLE_CONSTRAINTS = {
    # 操作: (前置条件检查函数, 违反时的用户提示, 引导操作)
    "delete_pool": (
        lambda ctx: no_teams_using_pool(ctx["pool_id"]),
        "该存储池仍有团队使用，无法删除",
        "查看占用的团队"
    ),
    "upload_file": (
        lambda ctx: is_space_member(ctx["user_id"], ctx["space_id"]),
        "请先加入团队或空间才能上传文件",
        "加入团队"
    ),
    "create_private_space": (
        lambda ctx: is_team_member(ctx["user_id"], ctx["parent_space_id"]),
        "只有团队成员才能申请私人空间",
        "加入团队"
    ),
    # ... 更多约束
}
```

### 前端拦截实现

```javascript
// 生命周期操作拦截器
class LifecycleInterceptor {
    constructor() {
        this.constraints = {
            upload_file: {
                check: (context) => context.isMember,
                message: "请先加入团队或空间才能上传文件",
                action: { label: "加入团队", path: "/teams" }
            },
            create_team: {
                check: (context) => context.hasPool,
                message: "系统暂无可用存储池，请联系管理员创建",
                action: { label: "创建存储池", path: "/admin/pools/create" }
            },
            // ... 更多约束
        };
    }

    // 执行操作前检查
    async beforeAction(action, context) {
        const constraint = this.constraints[action];
        if (!constraint) return true; // 无约束，放行

        const passed = await constraint.check(context);
        if (!passed) {
            this.showGuidanceModal({
                title: this.getTitle(action),
                message: constraint.message,
                action: constraint.action
            });
            return false;
        }
        return true;
    }

    getTitle(action) {
        const titles = {
            upload_file: "无法上传文件",
            create_team: "无法创建团队",
            delete_pool: "无法删除存储池",
            // ...
        };
        return titles[action] || "操作受限";
    }
}
```

---

## 用户语言提示设计

### 提示原则

1. **明确性**：直接说明什么问题
2. **可操作性**：告诉用户下一步怎么做
3. **友好性**：使用"请"、"您"等礼貌用语
4. **一致性**：相同错误使用相同提示

### 提示消息库

| 错误代码 | 用户提示 | 引导操作 |
|---------|---------|---------|
| `NOT_SPACE_MEMBER` | "您还没有加入任何团队，无法访问文件存储。请先加入一个团队或创建一个新团队。" | ["浏览团队", "创建团队"] |
| `POOL_NOT_FOUND` | "系统暂无可用存储池，请联系管理员创建存储池后再试。" | ["联系管理员"] |
| `QUOTA_EXCEEDED` | "您的存储配额已用尽，无法上传新文件。请清理回收站或联系管理员申请扩容。" | ["查看回收站", "申请扩容"] |
| `TEAM_QUOTA_EXCEEDED` | "团队存储配额已用尽，无法创建新文件。团队管理员可以清理回收站或调整配额。" | ["联系管理员"] |
| `NOT_TEAM_OWNER` | "只有团队所有者可以执行此操作。" | ["联系团队管理员"] |
| `PRIVATE_SPACE_REQUIRED` | "私人空间需要从团队空间申请。请先加入一个团队。" | ["加入团队"] |
| `STORAGE_POOL_IN_USE` | "该存储池仍有团队使用，无法删除。请先将团队迁移到其他存储池。" | ["查看使用中的团队"] |
| `INVALID_CREDENTIAL` | "邀请码已过期或无效，请联系团队管理员获取新邀请码。" | ["联系管理员"] |
| `MEMBER_LIMIT_EXCEEDED` | "团队成员数已达到上限，请联系管理员扩容。" | ["联系管理员"] |

---

## 后端约束实现

### 服务层约束检查

```python
# team_service.py
def delete_pool(self, pool_id: str) -> None:
    """删除存储池 (约束: 无团队使用)"""
    session = self._db()
    try:
        pool = session.query(StoragePool).filter(StoragePool.id == pool_id).first()
        if not pool:
            raise StoragePoolNotFound()

        # 约束检查: 是否有团队使用此池
        team_count = session.query(Team).filter(
            Team.storage_pool_id == pool_id
        ).count()

        if team_count > 0:
            # 获取使用此池的团队列表
            teams = session.query(Team).filter(
                Team.storage_pool_id == pool_id
            ).all()
            team_names = ", ".join([t.name for t in teams])

            raise LifecycleViolation(
                code="STORAGE_POOL_IN_USE",
                message=f"该存储池仍被以下团队使用: {team_names}，无法删除",
                details={
                    "pool_id": pool_id,
                    "teams": [t.to_dict() for t in teams]
                },
                guidance={
                    "action": "查看团队",
                    "url": "/admin/teams?pool_id={pool_id}"
                }
            )

        session.delete(pool)
        session.commit()
    finally:
        session.close()


class LifecycleViolation(Exception):
    """生命周期约束违反异常"""
    def __init__(self, code: str, message: str, details: dict = None, guidance: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.guidance = guidance or {}
        super().__init__(message)
```

---

## 前端错误处理

```javascript
// 统一的生命周期错误处理
function handleLifecycleError(error) {
    if (error.code === 'LIFECYCLE_VIOLATION') {
        const modal = new GuidanceModal({
            title: getErrorTitle(error.code),
            message: error.message,
            action: error.guidance?.action,
            onAction: () => {
                if (error.guidance?.url) {
                    router.push(error.guidance.url);
                }
            },
            onDismiss: () => modal.close()
        });
        modal.show();
        return;
    }

    // 其他错误走常规错误处理
    showErrorToast(error.message);
}
```

---

## 操作拦截流程图

```
用户操作
    │
    ▼
┌─────────────────┐
│ 前端拦截检查     │
│ (UI 层面快速检查) │
└────────┬────────┘
         │
    通过 │ 不通过
    │    │
    ▼    ▼
┌────┐ ┌─────────────────┐
│继续│ │ 显示引导弹窗     │
│    │ │ ( LifecycleModal)│
└────┘ └────────┬────────┘
                 │
                 ▼
         用户选择引导操作
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
执行引导操作              取消操作
(跳转/执行)              (关闭弹窗)
```

---

## 约束规则表

| 操作 | 前置条件 | 违反提示 | 引导操作 |
|------|---------|---------|---------|
| `upload_file` | 是 Space 成员 | "请先加入团队或空间才能上传文件" | ["加入团队", "创建团队"] |
| `create_team` | 有可用存储池 | "系统暂无可用存储池，请联系管理员创建" | ["联系管理员"] |
| `create_private` | 是团队成员 | "只有团队成员才能申请私人空间" | ["加入团队"] |
| `delete_pool` | 无团队使用 | "该存储池仍有团队使用，无法删除" | ["查看团队"] |
| `delete_space` | 无活跃成员 | "该空间仍有成员，无法删除" | ["移除成员"] |
| `invite_member` | 是 Space Owner | "只有空间所有者可以邀请成员" | ["联系管理员"] |
| `join_team` | 有有效凭证 | "邀请码已过期，请获取新邀请码" | ["联系管理员"] |

---

## 相关文档

- [系统架构文档](./SYSTEM_ARCHITECTURE.md)
- [Admin 控制台建议](./ADMIN_DASHBOARD.md)
- [前端拦截器实现](../web/lifecycle-interceptor.js) (待实现)