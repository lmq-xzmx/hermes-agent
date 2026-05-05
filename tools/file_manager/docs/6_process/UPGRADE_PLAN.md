# Hermes File Manager 系统升级方案

## 版本目标

**目标版本**: v2.0.0
**升级范围**: 核心功能增强 + 用户体验优化 + 管理体系完善

---

## 升级背景

基于现有架构文档分析，当前系统具备基础的文件管理和协作能力，但在以下方面存在提升空间：

| 现状 | 目标 | 差距分析 |
|------|------|---------|
| 基础文件管理 | 智能存储管理 | 缺乏可视化监控和预警 |
| 简单权限控制 | 完整 RBAC 体系 | 路径模式匹配未实现 |
| 手动引导 | 事件驱动引导 | 无引导引擎 |
| 单点操作 | 自动化工作流 | 工作流能力待增强 |

---

## 升级模块规划

```
┌─────────────────────────────────────────────────────────────────────┐
│                        升级架构总览                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐           │
│  │  模块一       │  │  模块二       │  │  模块三       │           │
│  │  Admin 控制台 │  │  生命周期约束 │  │  新手引导    │           │
│  │  可视化增强   │  │  操作合规     │  │  事件驱动    │           │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘           │
│          │                  │                  │                   │
│          └──────────────────┼──────────────────┘                   │
│                             │                                      │
│                    ┌────────▼────────┐                             │
│                    │   共享基础设施  │                             │
│                    │  - 约束引擎     │                             │
│                    │  - 引导引擎     │                             │
│                    │  - 事件总线     │                             │
│                    └─────────────────┘                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 模块一：Admin 控制台可视化增强

### 1.1 升级目标

- 实现存储池使用率环形图可视化
- 实现用户-空间关系桑基图
- 实现配额告警热力图
- 实现操作趋势折线图

### 1.2 技术方案

**后端 Python Service** (已在 `services/admin_analytics_service.py` 实现):
```python
# AdminAnalyticsService - 后端数据聚合服务
class AdminAnalyticsService:
    """Admin 数据分析服务"""

    def get_storage_summary(self) -> Dict[str, Any]:
        """存储池概览数据"""
        pools = self.team_service.list_pools()
        return {
            "total_pools": len(pools),
            "total_bytes": sum(p["total_bytes"] for p in pools),
            "used_bytes": sum(p["total_bytes"] - p["free_bytes"] for p in pools),
            "pools": [{
                "id": p["id"],
                "name": p["name"],
                "usage_rate": (p["total_bytes"] - p["free_bytes"]) / p["total_bytes"] if p["total_bytes"] > 0 else 0,
                "status": "critical" if usage_rate > 0.9 else "warning" if usage_rate > 0.7 else "normal"
            } for p in pools]
        }

    def get_user_space_relationships(self) -> List[Dict]:
        """用户-空间关系数据（桑基图）"""
        users = self.user_service.list_users()
        relationships = []
        for user in users:
            memberships = self.space_service.list_user_memberships(user["id"])
            for m in memberships:
                relationships.append({
                    "source": f"user:{user['id']}",
                    "target": f"space:{m['space_id']}",
                    "role": m["role"]
                })
        return relationships

    def get_quota_heatmap(self) -> Dict[str, List]:
        """配额告警热力图数据"""
        spaces = self.space_service.list_spaces()
        heatmap = {}
        for space in spaces:
            usage_rate = space["used_bytes"] / space["max_bytes"] if space["max_bytes"] > 0 else 0
            status = "critical" if usage_rate > 0.8 else "warning" if usage_rate > 0.6 else "normal"
            if status != "normal":
                heatmap[space["id"]] = {
                    "name": space["name"],
                    "usage_rate": usage_rate,
                    "status": status
                }
        return heatmap
```

**前端 Vue Composable** (已在 `web/src/services/adminAnalytics.js` 实现):
```javascript
// useAdminAnalytics - Vue 3 Composition API composable
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useAdminAnalytics = () => {
  const storageSummary = ref(null)
  const userSpaceRelationships = ref([])
  const quotaHeatmap = ref({})
  const loading = ref(false)
  const error = ref(null)

  const fetchStorageSummary = async () => {
    loading.value = true
    try {
      const response = await fetch('/api/v1/admin/analytics/storage')
      storageSummary.value = await response.json()
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  const fetchUserSpaceRelationships = async () => {
    const response = await fetch('/api/v1/admin/analytics/relationships')
    userSpaceRelationships.value = await response.json()
  }

  const fetchQuotaHeatmap = async () => {
    const response = await fetch('/api/v1/admin/analytics/quota-heatmap')
    quotaHeatmap.value = await response.json()
  }

  const usageRate = computed(() => {
    if (!storageSummary.value) return 0
    const { total_bytes, used_bytes } = storageSummary.value
    return total_bytes > 0 ? used_bytes / total_bytes : 0
  })

  return {
    storageSummary,
    userSpaceRelationships,
    quotaHeatmap,
    loading,
    error,
    usageRate,
    fetchStorageSummary,
    fetchUserSpaceRelationships,
    fetchQuotaHeatmap
  }
}
```

### 1.3 实施步骤

```
阶段1: 数据层 (第1-2周)
├── 实现 AdminAnalyticsService
├── 添加 /api/v1/admin/analytics/* 接口
└── 编写单元测试

阶段2: 前端组件 (第3-4周)
├── 引入 ECharts 图表库
├── 实现 StoragePoolRingChart 组件
├── 实现 UserSpaceSankey 组件
└── 实现 QuotaHeatmap 组件

阶段3: 集成 (第5-6周)
├── Admin 控制台页面重构
├── 实时数据 WebSocket 推送
└── 告警通知集成
```

### 1.4 预估工作量

| 阶段 | 工作项 | 人天 |
|------|--------|------|
| 数据层 | Analytics Service + API | 3 |
| 前端 | 图表组件开发 | 5 |
| 集成 | 控制台集成 + 测试 | 3 |
| **合计** | | **11 人天** |

---

## 模块二：生命周期操作约束

### 2.1 升级目标

- 实现前端操作拦截器
- 实现后端约束验证
- 实现用户友好的错误提示
- 实现引导操作重定向

### 2.2 技术方案

```python
# 后端约束异常定义
class LifecycleViolation(Exception):
    """生命周期约束违反异常"""
    def __init__(self, code: str, message: str, details: dict = None, guidance: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.guidance = guidance or {}
        super().__init__(message)

# 约束检查装饰器
def lifecycle_constraint(check_fn, error_code, error_message, guidance_action):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = check_fn(*args, **kwargs)
            if not context["passed"]:
                raise LifecycleViolation(
                    code=error_code,
                    message=error_message,
                    details=context.get("details"),
                    guidance={"action": guidance_action, "url": context.get("redirect_url")}
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@route("/api/v1/pools/{pool_id}", method="DELETE")
@lifecycle_constraint(
    check_fn=lambda pool_id: check_no_teams_using_pool(pool_id),
    error_code="STORAGE_POOL_IN_USE",
    error_message="该存储池仍有团队使用，无法删除",
    guidance_action="view_teams"
)
async def delete_pool(pool_id: str):
    """删除存储池"""
    pass
```

```javascript
// useLifecycleInterceptor - Vue 3 Composition API composable
// 已在 web/src/interceptors/lifecycle-interceptor.js 实现
import { ref } from 'vue'
import { useGuidance } from '@/composables/useGuidance'

export const useLifecycleInterceptor = () => {
  const constraints = ref({
    upload_file: {
      check: (context) => context.isMember,
      message: "请先加入团队或空间才能上传文件",
      action: { label: "加入团队", path: "/teams" }
    },
    create_team: {
      check: (context) => context.hasAvailablePool,
      message: "系统暂无可用存储池，请联系管理员创建",
      action: { label: "联系管理员", path: "/admin" }
    },
    // ... 更多约束
  })

  const showGuidanceModal = ({ title, message, action }) => {
    // 调用 guidance modal 组件
    const { trigger } = useGuidance()
    trigger('lifecycle_violation', { title, message, action })
  }

  const beforeAction = async (action, context) => {
    const constraint = constraints.value[action]
    if (!constraint) return true

    const passed = await constraint.check(context)
    if (!passed) {
      showGuidanceModal({
        title: `无法执行操作`,
        message: constraint.message,
        action: constraint.action
      })
      return false
    }
    return true
  }

  const getActionName = (action) => {
    const names = {
      upload_file: '上传',
      create_team: '创建团队',
      create_private: '申请',
      delete_pool: '删除',
      delete_space: '删除',
      invite_member: '邀请'
    }
    return names[action] || action
  }

  return {
    constraints,
    beforeAction,
    showGuidanceModal,
    getActionName
  }
}
```

### 2.3 约束规则表

| 操作 | 前置条件 | 错误码 | 用户提示 |
|------|---------|--------|---------|
| `upload_file` | 是 Space 成员 | `NOT_SPACE_MEMBER` | "请先加入团队或空间才能上传文件" |
| `create_team` | 有可用存储池 | `NO_AVAILABLE_POOL` | "系统暂无可用存储池，请联系管理员创建" |
| `create_private` | 是团队成员 | `NOT_TEAM_MEMBER` | "只有团队成员才能申请私人空间" |
| `delete_pool` | 无团队使用 | `STORAGE_POOL_IN_USE` | "该存储池仍有团队使用，无法删除" |
| `delete_space` | 无活跃成员 | `SPACE_HAS_MEMBERS` | "该空间仍有成员，无法删除" |
| `invite_member` | 是 Space Owner | `NOT_SPACE_OWNER` | "只有空间所有者可以邀请成员" |

### 2.4 实施步骤

```
阶段1: 后端约束 (第1-2周)
├── 定义 LifecycleViolation 异常
├── 实现约束检查装饰器
├── 为所有危险操作添加约束
└── 编写集成测试

阶段2: 前端拦截 (第3-4周)
├── 实现 LifecycleInterceptor 类
├── 在关键操作入口添加拦截检查
├── 实现 GuidanceModal 组件
└── UI 联调

阶段3: 测试与文档 (第5周)
├── 约束规则测试覆盖
├── 用户提示文案审核
└── 操作手册更新
```

### 2.5 预估工作量

| 阶段 | 工作项 | 人天 |
|------|--------|------|
| 后端约束 | 异常类 + 装饰器 + 规则 | 4 |
| 前端拦截 | 拦截器 + 引导弹窗 | 3 |
| 联调测试 | 全流程测试 | 2 |
| **合计** | | **9 人天** |

---

## 模块三：事件驱动新手引导

### 3.1 升级目标

- 实现引导事件触发引擎
- 实现 8 个核心引导节点
- 实现引导 UI 组件（Modal + Coach Mark）
- 集成工作流和笔记本功能引导

### 3.2 技术方案

**后端引导引擎** (已在 `services/guidance_engine.py` 实现):
```python
# GuidanceEngine - 后端引导事件处理
class GuidanceEngine:
    """引导事件触发引擎"""

    def __init__(self, lifecycle_interceptor):
        self.interceptor = lifecycle_interceptor

    def trigger(self, event, context):
        """触发引导事件"""
        # 某些引导依赖于约束检查结果
        if event == "QUOTA_WARNING":
            constraint_result = self.interceptor.check_quota(context)
            context["quota_details"] = constraint_result
        # ... 事件处理逻辑
```

**前端引导 Composable** (已在 `web/src/composables/useGuidance.js` 实现):
```javascript
// useGuidance - Vue 3 Composition API composable
// 引导引擎核心实现
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

export const useGuidance = () => {
  const router = useRouter()
  const events = ref(new Map())
  const context = ref({})
  const dismissedEvents = ref(new Set())

  // 引导事件定义
  const guidanceEvents = {
    USER_REGISTERED: {
      title: "欢迎使用 Hermes File Manager",
      message: "您已成功注册！首先创建一个团队或加入现有团队开始存储文件。",
      actions: [
        { label: "创建我的团队", action: "CREATE_TEAM", icon: "👥" },
        { label: "浏览现有团队", action: "LIST_TEAMS", icon: "🔍" }
      ],
      condition: (ctx) => ctx.teams?.length === 0
    },

    FIRST_FILE_UPLOADED: {
      title: "文件上传成功！",
      message: "了解如何与团队成员协作编辑和分享文件",
      actions: [
        { label: "分享给成员", action: "SHARE_FILE", icon: "🔗" },
        { label: "查看版本历史", action: "VIEW_VERSIONS", icon: "📜" },
        { label: "创建工作流", action: "CREATE_WORKFLOW", icon: "⚙️" }
      ],
      condition: (ctx) => ctx.uploadCount === 1
    },
    // ... 更多事件
  }

  const register = (eventName, config) => {
    events.value.set(eventName, config)
  }

  const trigger = (event, ctx = {}) => {
    const config = events.value.get(event) || guidanceEvents[event]
    if (!config) return

    // 检查触发条件
    if (config.condition && !config.condition(ctx)) {
      return
    }

    // 检查是否已忽略
    if (isDismissed(event)) return

    showGuidance(config)
  }

  const isDismissed = (event) => {
    return dismissedEvents.value.has(event)
  }

  const dismiss = (event) => {
    dismissedEvents.value.add(event)
    // 持久化到 localStorage
    localStorage.setItem(`guidance_dismissed_${event}`, 'true')
  }

  const showGuidance = (config) => {
    // 调用 GuidanceModal 组件
    // modal.show() - 由组件内部处理
  }

  const executeAction = (action) => {
    const actions = {
      "CREATE_TEAM": () => router.push("/teams/create"),
      "LIST_TEAMS": () => router.push("/teams"),
      "SHARE_FILE": () => showShareDialog(),
      // ...
    }
    const handler = actions[action]
    if (handler) handler()
  }

  // 初始化引导事件
  Object.entries(guidanceEvents).forEach(([name, config]) => {
    register(name, config)
  })

  return {
    events,
    context,
    register,
    trigger,
    dismiss,
    isDismissed,
    showGuidance,
    executeAction
  }
}

// 使用示例
// 在 Vue 组件中:
// const { trigger } = useGuidance()
// trigger('FIRST_FILE_UPLOADED', { uploadCount: 1, spaceId: 'xxx' })
```
```

### 3.3 引导事件定义

| 事件 | 触发时机 | 条件 | 引导内容 |
|------|---------|------|---------|
| USER_REGISTERED | 注册成功 | 无团队 | 引导创建/加入团队 |
| TEAM_JOINED | 加入团队 | 首次加入 | 引导上传文件 |
| FIRST_FILE_UPLOADED | 文件上传成功 | 上传数=1 | 引导协作功能 |
| MEMBER_INVITED | 邀请发送成功 | 成员数>1 | 引导权限设置 |
| WORKFLOW_EXECUTED | 工作流执行成功 | 首次执行 | 引导笔记本 |
| QUOTA_WARNING | 配额>80% | 超80%阈值 | 引导清理/扩容 |
| PRIVATE_SPACE_PENDING | 私人空间待审核 | 申请中 | 引导创建笔记 |
| CROSS_TEAM_COLLAB | 跨团队协作建立 | 跨团队数>0 | 引导高级功能 |

### 3.4 工作流引导集成

```javascript
// 工作流创建引导
guidance.register("WORKFLOW_CREATE_GUIDE", {
    steps: [
        {
            target: "#workflowTab",
            content: "点击「工作流」标签"
        },
        {
            target: "#newWorkflowBtn",
            content: "点击「+ 新建工作流」"
        },
        {
            target: "#workflowTemplate",
            content: "选择「文件归档流程」模板"
        },
        {
            target: "#workflowSave",
            content: "配置步骤并保存"
        }
    ]
});
```

### 3.5 实施步骤

```
阶段1: 引导引擎 (第1-2周)
├── 实现 GuidanceEngine 核心类
├── 定义 8 个引导事件
├── 实现 GuidanceModal 组件
└── 单元测试

阶段2: 触发点集成 (第3-4周)
├── 在关键操作添加触发点
├── 实现引导上下文收集
├── 引导状态持久化（localStorage）
└── 联调测试

阶段3: 工作流/笔记本引导 (第5周)
├── 工作流创建引导 Tour
├── 笔记本协作引导
└── 新手任务清单
```

### 3.6 预估工作量

| 阶段 | 工作项 | 人天 |
|------|--------|------|
| 引导引擎 | 引擎 + 事件 + Modal | 4 |
| 触发点 | 关键操作集成 | 3 |
| 功能引导 | 工作流 + 笔记本引导 | 2 |
| **合计** | | **9 人天** |

---

## 模块四：共享基础设施

### 4.1 约束引擎复用

引导引擎需要复用约束引擎的基础设施：

```python
# 共享的事件和异常
from .lifecycle_engine import LifecycleViolation, ConstraintRule

# 引导引擎依赖约束引擎的检查结果
class GuidanceEngine:
    def __init__(self, lifecycle_interceptor):
        self.interceptor = lifecycle_interceptor

    def trigger(self, event, context):
        # 某些引导依赖于约束检查结果
        if event == "QUOTA_WARNING":
            constraint_result = self.interceptor.check_quota(context)
            context["quota_details"] = constraint_result
```

### 4.2 事件总线

```python
# 共享事件总线
class EventBus:
    # 生命周期事件
    LIFECYCLE_VIOLATION = "lifecycle:violation"

    # 引导事件
    GUIDANCE_TRIGGER = "guidance:trigger"

    # 系统事件
    QUOTA_WARNING = "quota:warning"
    SYSTEM_READY = "system:ready"
```

---

## 升级实施计划

### 时间规划

```
第1周     第2周     第3周     第4周     第5周     第6周
─────────┼─────────┼─────────┼─────────┼─────────┼─────────
模块一: Admin 控制台
├── 数据层
│           └── 前端组件
│                     └── 集成
模块二: 生命周期约束
          └── 后端约束
                      └── 前端拦截
                                  └── 测试
模块三: 新手引导
                    └── 引导引擎
                              └── 触发点
                                        └── 功能引导
模块四: 共享基础设施 (贯穿全程)
```

### 里程碑

| 里程碑 | 完成时间 | 交付内容 |
|--------|---------|---------|
| M1 | 第2周末 | 约束引擎 + Admin 数据层 |
| M2 | 第4周末 | 前端拦截 + 图表组件 |
| M3 | 第5周末 | 引导引擎 + 触发点 |
| M4 | 第6周末 | 全流程测试 + 发布 |

---

## 测试计划

### 单元测试

```python
# test_lifecycle_constraints.py
def test_delete_pool_with_teams_fails():
    """删除有团队使用的存储池应失败"""
    create_team_with_pool(pool_id="pool-1", team_id="team-1")
    with pytest.raises(LifecycleViolation) as exc:
        delete_pool("pool-1")
    assert exc.value.code == "STORAGE_POOL_IN_USE"

def test_upload_file_without_membership_fails():
    """非成员上传文件应被拦截"""
    user = create_user()
    space = create_space()
    with pytest.raises(LifecycleViolation) as exc:
        upload_file(user_id=user.id, space_id=space.id)
    assert exc.value.code == "NOT_SPACE_MEMBER"
```

### 集成测试

```javascript
// e2e/guidance.spec.js
test("新手引导完整流程", async () => {
    // 1. 注册新用户
    await registerNewUser();

    // 2. 验证引导触发
    const modal = await waitForGuidanceModal();
    expect(modal.title).toBe("欢迎使用 Hermes File Manager");

    // 3. 点击创建团队
    await modal.clickAction("创建我的团队");
    expect(page.url()).toContain("/teams/create");
});
```

---

## 回滚方案

### 回滚触发条件

- 测试覆盖率 < 80%
- 任何模块单元测试失败 > 5%
- 关键路径集成测试失败
- 用户报告阻塞性 bug

### 回滚步骤

```bash
# 回滚到 v1.x
git checkout v1.0.0
cargo build --release
# 重新部署
```

---

## 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 引导引擎影响性能 | 低 | 中 | 异步加载，事件节流 |
| 约束拦截误伤正常操作 | 中 | 高 | 充分测试，灰度发布 |
| 图表渲染影响 UI | 低 | 中 | 使用虚拟化，长列表优化 |

---

## 成本估算

| 模块 | 开发 | 测试 | 总计 |
|------|------|------|------|
| Admin 控制台 | 8 人天 | 3 人天 | 11 人天 |
| 生命周期约束 | 6 人天 | 3 人天 | 9 人天 |
| 新手引导 | 6 人天 | 3 人天 | 9 人天 |
| 共享基础设施 | 3 人天 | 1 人天 | 4 人天 |
| **总计** | **23 人天** | **10 人天** | **33 人天** |

---

## 相关文档

- [系统架构文档](./docs/architecture/SYSTEM_ARCHITECTURE.md)
- [Admin 控制台建议](./docs/architecture/ADMIN_DASHBOARD.md)
- [生命周期约束](./docs/architecture/LIFECYCLE_CONSTRAINTS.md)
- [新手指导](./docs/architecture/NEW_USER_GUIDE.md)

---

## 实现状态 (2026-05-05 更新)

### Vue 3 迁移状态 ✅ 已完成

| 组件 | 旧路径 (Vanilla JS) | 新路径 (Vue 3) | 状态 |
|------|---------------------|----------------|------|
| 主入口 | `app.html` | `vue.html` | ✅ 已迁移 |
| 平台适配器 | `web/js/platform-adapter.js` | `src/platformAdapter.js` | ✅ 已迁移 |
| GuidanceModal | `web/js/components/GuidanceModal.js` | `web/src/components/common/GuidanceModal.vue` | ✅ 已清理 |
| NotebookTourGuide | `web/js/components/NotebookTour.js` | `web/src/components/NotebookTourGuide.vue` | ✅ 已清理 |
| WorkflowTourGuide | `web/js/components/WorkflowTour.js` | `web/src/components/admin/WorkflowTourGuide.vue` | ✅ 已清理 |

> 📝 `app.html` 已标注为废弃页面，指向 `vue.html` 作为唯一入口

### 已实现模块

| 模块 | 组件 | 路径 | 状态 |
|------|------|------|------|
| **模块一** | AdminAnalyticsService | `services/admin_analytics_service.py` | ✅ |
| | StoragePoolChart | `web/src/components/admin/StoragePoolChart.vue` | ✅ |
| | UserSpaceSankey | `web/src/components/admin/UserSpaceSankey.vue` | ✅ |
| | QuotaHeatmap | `web/src/components/admin/QuotaHeatmap.vue` | ✅ |
| | OperationTrends | `web/src/components/admin/OperationTrends.vue` | ✅ |
| | AlertList | `web/src/components/admin/AlertList.vue` | ✅ |
| | AdminOverview | `web/src/components/admin/AdminOverview.vue` | ✅ |
| **模块二** | LifecycleViolation | `engine/lifecycle_exception.py` | ✅ |
| | lifecycle_constraint 装饰器 | `services/lifecycle_engine.py` | ✅ |
| | LifecycleInterceptor | `web/src/interceptors/lifecycle-interceptor.js` | ✅ 已迁移到 src |
| **模块三** | GuidanceEngine (后端) | `services/guidance_engine.py` | ✅ |
| | GuidanceModal | `web/src/components/common/GuidanceModal.vue` | ✅ |
| | NotebookTourGuide | `web/src/components/NotebookTourGuide.vue` | ✅ |
| | WorkflowTourGuide | `web/src/components/admin/WorkflowTourGuide.vue` | ✅ |
| | useGuidance | `web/src/composables/useGuidance.js` | ✅ |
| **模块四** | EventBus | `services/event_bus.py` | ✅ |
| | 约束引擎复用 | `services/lifecycle_engine.py` | ✅ |
| **Vue 3 迁移** | vue.html 主入口 | `web/vue.html` | ✅ |
| | platformAdapter | `web/src/platformAdapter.js` | ✅ |
| | 浮窗入口 | `web/floating-vue.html` | ✅ |

### 未完成项 (G9 实施中)

| 任务 | 说明 | 优先级 | 状态 |
|------|------|--------|------|
| 引导状态持久化 | localStorage 存储引导完成状态 | 中 | ✅ 已完成 |
| 工作流引导 Tour | 工作流创建引导 Tour | 低 | ✅ 已完成 |
| 笔记本引导 | 笔记本协作编辑引导 | 低 | ✅ 已完成 |
| 配额超卖防护 | SELECT FOR UPDATE 锁定 | P0 | ✅ 已完成 |
| 并发邀请防护 | 唯一索引防护 | P0 | ✅ 已完成 |
| WebSocket 实时推送 | Admin 实时数据更新 | 中 | ✅ 已完成 |

### 总体完成度

```
████████████████████████████  100%

G1-G8: 100% ✅
G9: 实施中 (配额超卖、并发邀请、监控告警、审计日志)
Vue 3 迁移: 100% ✅
```