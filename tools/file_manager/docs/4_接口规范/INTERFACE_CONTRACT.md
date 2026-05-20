# 接口契约文档 (Interface Contract)

> **版本**: 1.4
> **更新日期**: 2026-05-06
> **目的**: 定义前后端、WebSocket、EventBus 的接口契约，确保集成一致性
> **更新说明 v1.4**: 新增 Knowledge API (1.4)，文档同步和搜索端点
> **更新说明 v1.3**: 新增 Storage Pool API (1.2)，包含 CRUD + cleanup 端点

---

## 一、REST API 契约

### 1.1 Admin Analytics API

#### GET /api/v1/admin/analytics/overview

**请求**
```
Headers:
  Authorization: Bearer <token>
```

**响应**
```json
{
  "summary": {
    "total_users": 128,
    "active_users_7d": 89,
    "new_users_7d": 12,
    "total_teams": 24,
    "total_spaces": 156,
    "total_pools": 3,
    "storage": {
      "total_bytes": 21474836480000,
      "used_bytes": 9663676416000,
      "free_bytes": 11811160064000,
      "usage_rate": 0.45
    }
  },
  "alerts": [
    {
      "id": "alert_001",
      "type": "quota_warning",
      "level": "warning",
      "resource": "Space",
      "resource_id": "space_123",
      "resource_name": "Team-A 项目空间",
      "usage_rate": 0.82,
      "message": "空间配额使用率超过80%",
      "created_at": "2026-05-02T10:00:00Z"
    }
  ]
}
```

#### GET /api/v1/admin/analytics/storage-pools

**请求**
```
Headers:
  Authorization: Bearer <token>
```

**响应**
```json
{
  "pools": [
    {
      "id": "pool_001",
      "name": "本地存储池 A",
      "protocol": "local",
      "base_path": "/data/pool-a",
      "total_bytes": 10737418240000,
      "used_bytes": 6442450944000,
      "free_bytes": 4294967296000,
      "usage_rate": 0.60,
      "team_count": 8,
      "status": "normal"
    }
  ],
  "summary": {
    "total_pools": 3,
    "total_bytes": 32212254720000,
    "used_bytes": 16106127360000
  }
}
```

---

### 1.2 Storage Pool API

#### GET /api/v1/pools

获取存储池列表。

**请求**
```
Headers:
  Authorization: Bearer <token>
```

**响应** (200)
```json
{
  "pools": [
    {
      "pool_id": "pool_001",
      "name": "本地存储池 A",
      "type": "standard",
      "status": "active",
      "total_bytes": 10737418240000,
      "used_bytes": 6442450944000,
      "free_bytes": 4294967296000,
      "usage_ratio": 0.60,
      "description": "标准存储池",
      "created_at": "2026-05-01T10:00:00Z"
    }
  ],
  "total": 3
}
```

---

#### POST /api/v1/pools

创建存储池。

**请求**
```json
{
  "name": "本地存储池 A",
  "type": "standard",
  "total_bytes": 10737418240000,
  "description": "标准存储池"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 存储池名称 |
| `type` | string | ✅ | 类型: standard, high-performance, archival |
| `total_bytes` | integer | ✅ | 总容量（字节） |
| `description` | string | ❌ | 描述 |

**成功响应** (201)
```json
{
  "pool_id": "pool_001",
  "name": "本地存储池 A",
  "type": "standard",
  "status": "active",
  "total_bytes": 10737418240000,
  "used_bytes": 0,
  "free_bytes": 10737418240000,
  "usage_ratio": 0,
  "description": "标准存储池",
  "created_at": "2026-05-06T10:00:00Z"
}
```

---

#### GET /api/v1/pools/{pool_id}

获取存储池详情。

**响应** (200)
```json
{
  "pool_id": "pool_001",
  "name": "本地存储池 A",
  "type": "standard",
  "status": "active",
  "total_bytes": 10737418240000,
  "used_bytes": 6442450944000,
  "free_bytes": 4294967296000,
  "usage_ratio": 0.60,
  "description": "标准存储池",
  "team_count": 8,
  "team_migrating_count": 0,
  "created_at": "2026-05-01T10:00:00Z",
  "updated_at": "2026-05-05T15:30:00Z"
}
```

---

#### PUT /api/v1/pools/{pool_id}

更新存储池。

**请求**
```json
{
  "name": "本地存储池 A (已更新)",
  "type": "high-performance",
  "description": "高性能存储池"
}
```

**成功响应** (200)
```json
{
  "pool_id": "pool_001",
  "name": "本地存储池 A (已更新)",
  "type": "high-performance",
  "status": "active",
  "message": "存储池已更新"
}
```

---

#### DELETE /api/v1/pools/{pool_id}

删除存储池。

**约束检查响应** (409)
```json
{
  "code": "STORAGE_POOL_IN_USE",
  "message": "该存储池仍有团队使用，无法删除",
  "details": {
    "team_count": 3
  },
  "guidance": {
    "label": "查看团队",
    "icon": "👥",
    "action_type": "navigate",
    "path": "/admin/teams"
  }
}
```

```json
{
  "code": "POOL_TEAMS_MIGRATING",
  "message": "该存储池有团队正在迁移中",
  "details": {
    "team_migrating_count": 1
  },
  "guidance": {
    "label": "查看迁移进度",
    "icon": "🔄",
    "action_type": "navigate",
    "path": "/admin/teams?status=migrating"
  }
}
```

**成功响应** (200)
```json
{
  "message": "存储池已删除"
}
```

---

#### POST /api/v1/pools/{pool_id}/cleanup

清理存储池临时文件。

**请求**
```json
{
  "scope": "temp"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scope` | string | ✅ | 清理范围: temp (临时文件) |

**成功响应** (200)
```json
{
  "message": "清理完成",
  "cleaned_bytes": 1073741824,
  "pool_id": "pool_001"
}
```

---

### 1.3 Lifecycle API

#### POST /api/v1/teams

**请求**
```json
{
  "name": "Team-A",
  "storage_pool_id": "pool_001",
  "max_bytes": 10737418240000
}
```

**成功响应** (201)
```json
{
  "id": "team_001",
  "name": "Team-A",
  "storage_pool_id": "pool_001",
  "max_bytes": 10737418240000,
  "owner_id": "user_001",
  "created_at": "2026-05-02T10:00:00Z"
}
```

**约束违反响应** (409)
```json
{
  "code": "NO_AVAILABLE_POOL",
  "message": "系统暂无可用存储池，无法创建新团队",
  "details": {},
  "guidance": {
    "label": "联系管理员",
    "icon": "📧",
    "action_type": "callback",
    "callback": "showContactAdminModal"
  }
}
```

---

### 1.4 Knowledge API

知识库 API 用于与 LLM Wiki 服务集成，实现文档同步和搜索功能。

#### GET /api/v1/knowledge/status

检查 llm_wiki 服务状态。

**请求**
```
Headers:
  Authorization: Bearer <token>
```

**成功响应** (200)
```json
{
  "running": true,
  "sync_mode": "manual"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `running` | boolean | llm_wiki API 服务是否运行中 |
| `sync_mode` | string | 当前同步模式: "manual" |

---

#### POST /api/v1/knowledge/sync

同步文档到知识库。

**请求**
```json
{
  "source_path": "/path/to/sync",
  "project_name": "default"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source_path` | string | 是 | 要同步的文件或文件夹路径 |
| `project_name` | string | 否 | 目标项目名称，默认 "default" |

**Headers**
```
Authorization: Bearer <token>
```

**成功响应** (200)
```json
{
  "job_id": "uuid-string",
  "status": "pending",
  "source_path": "/path/to/sync",
  "target_project": "default"
}
```

**错误响应** (403)
```json
{
  "detail": "只有空间成员才能同步文档到知识库"
}
```

**权限**: 空间成员或管理员

---

#### GET /api/v1/knowledge/search

搜索知识库。

**请求**
```
GET /api/v1/knowledge/search?q=<query>&project=<project>
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `q` | string | 是 | 搜索关键词 |
| `project` | string | 否 | 项目名称，默认 "default" |

**Headers**
```
Authorization: Bearer <token>
```

**成功响应** (200)
```json
{
  "results": [
    {
      "id": "uuid-string",
      "title": "文档标题",
      "snippet": "搜索结果摘要...",
      "score": 0.95,
      "path": "/path/to/document"
    }
  ]
}
```

**错误响应** (403)
```json
{
  "detail": "只有空间成员才能搜索知识库"
}
```

**权限**: 空间成员或管理员

---

#### POST /api/v1/llm_wiki/open

打开 LLM Wiki GUI（辅助端点）。

**请求**: 无

**成功响应** (200)
```json
{
  "message": "LLM Wiki opened"
}
```

---

## 二、WebSocket 消息契约

### 2.1 连接

**Endpoint**: `ws://host/ws/admin/analytics?token=<jwt_token>`

**认证失败** (4001)
```json
{
  "type": "error",
  "code": "UNAUTHORIZED",
  "message": "Unauthorized"
}
```

**连接成功**
```json
{
  "type": "connected",
  "session_id": "sess_abc123",
  "timestamp": "2026-05-02T10:00:00Z"
}
```

### 2.2 心跳机制

**心跳配置**:
| 参数 | 值 | 说明 |
|------|-----|------|
| 服务端心跳间隔 | 30s | 服务端主动发送 ping |
| 客户端响应超时 | 10s | 超时未响应则断开 |
| 断线重连间隔 | 5s | 指数退避最大 60s |
| 最大重试次数 | 无限 | 持续重连 |

**Ping (服务端 → 客户端)**:
```json
{
  "type": "ping"
}
```

**Pong (客户端 → 服务端)**:
```json
{
  "type": "pong"
}
```

**注意**: 客户端也可主动发送 ping，服务端会响应 pong。

### 2.3 客户端发送

**Ping** (客户端主动)
```json
{
  "type": "ping"
}
```

**订阅特定数据类型** (可选)
```json
{
  "type": "subscribe",
  "channels": ["analytics", "alerts"]
}
```

### 2.4 服务器推送

**Analytics Update** (每30秒自动推送)
```json
{
  "type": "analytics_update",
  "data": {
    "overview": {
      "total_users": 128,
      "active_users_7d": 89,
      "new_users_7d": 12,
      "total_teams": 24,
      "total_spaces": 156,
      "total_pools": 3,
      "storage": {
        "total_bytes": 21474836480000,
        "used_bytes": 9663676416000,
        "free_bytes": 11811160064000,
        "usage_rate": 0.45
      }
    },
    "alerts": [
      {
        "id": "alert_001",
        "type": "quota_warning",
        "level": "warning",
        "resource": "Space",
        "resource_id": "space_123",
        "resource_name": "Team-A 项目空间",
        "usage_rate": 0.82,
        "message": "空间配额使用率超过80%",
        "created_at": "2026-05-02T10:00:00Z"
      }
    ],
    "recent_activities": [
      {
        "id": "act_001",
        "user_id": "user_456",
        "username": "张三",
        "action": "file_upload",
        "target": "space_123",
        "target_name": "Team-A 项目空间",
        "result": "success",
        "created_at": "2026-05-02T11:30:00Z"
      }
    ]
  },
  "timestamp": "2026-05-02T10:00:00Z"
}
```

**Storage Pool Update** (存储池数据变化时推送)
```json
{
  "type": "storage_pool_update",
  "data": {
    "pool_id": "pool_001",
    "name": "本地存储池 A",
    "used_bytes": 6442450944000,
    "free_bytes": 4294967296000,
    "usage_rate": 0.60,
    "status": "normal"
  },
  "timestamp": "2026-05-02T10:00:00Z"
}
```

**Quota Warning**
```json
{
  "type": "quota_warning",
  "data": {
    "space_id": "space_001",
    "space_name": "项目A",
    "usage_rate": 0.85,
    "message": "空间配额使用率超过80%"
  },
  "timestamp": "2026-05-02T10:00:00Z"
}
```

**Lifecycle Violation**
```json
{
  "type": "lifecycle_violation",
  "data": {
    "code": "QUOTA_EXCEEDED",
    "message": "存储配额已用尽"
  },
  "timestamp": "2026-05-02T10:00:00Z"
}
```

---

## 三、EventBus 事件契约

### 3.1 事件类型枚举

```python
class EventType(Enum):
    # 生命周期事件
    LIFECYCLE_VIOLATION = "lifecycle:violation"
    QUOTA_WARNING = "quota:warning"
    QUOTA_EXCEEDED = "quota:exceeded"

    # 用户事件
    USER_REGISTERED = "user:registered"
    TEAM_JOINED = "team:joined"
    FILE_UPLOADED = "file:uploaded"

    # 系统事件
    SYSTEM_READY = "system:ready"
    POOL_CREATED = "pool:created"
    SPACE_CREATED = "space:created"
```

### 3.2 事件数据结构

```python
@dataclass
class Event:
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    source: str  # 模块名称
```

### 3.3 事件订阅示例

```python
# 订阅配额警告事件
event_bus.subscribe(EventType.QUOTA_WARNING, on_quota_warning_handler)

# 订阅生命周期违规事件
event_bus.subscribe(EventType.LIFECYCLE_VIOLATION, on_lifecycle_violation_handler)
```

---

## 四、Guidance 事件契约

### 4.1 触发事件名称常量

#### Python 端 (GuidanceEvent 枚举)

```python
class GuidanceEvent(str, Enum):
    """Guidance trigger events."""
    # Auth events
    USER_REGISTER = "guidance.user_register"
    USER_LOGIN = "guidance.user_login"

    # Space/Team events
    TEAM_CREATED = "guidance.team_created"
    SPACE_CREATED = "guidance.space_created"
    MEMBER_INVITED = "guidance.member_invited"

    # File operations
    FIRST_FILE_UPLOAD = "guidance.first_file_upload"
    FILE_UPLOAD_COMPLETE = "guidance.file_upload_complete"

    # Tour events
    TOUR_START = "guidance.tour_start"
    TOUR_COMPLETE = "guidance.tour_complete"
    TOUR_STEP = "guidance.tour_step"
```

#### 前端 (JavaScript)

```javascript
export const GUIDANCE_EVENTS = {
  USER_REGISTERED: 'user_registered',
  TEAM_JOINED: 'team_joined',
  FIRST_FILE_UPLOADED: 'first_file_uploaded',
  MEMBER_INVITED: 'member_invited',
  WORKFLOW_EXECUTED: 'workflow_executed',
  QUOTA_WARNING: 'quota_warning',
  PRIVATE_SPACE_PENDING: 'private_space_pending',
  CROSS_TEAM_COLLAB: 'cross_team_collab'
}
```

### 4.2 引导数据结构

```python
@dataclass
class GuidanceStep:
    """引导步骤"""
    id: str
    title: str
    content: str
    target_selector: str      # CSS 选择器
    position: str            # top/bottom/left/right
    button_text: str
    button_action: str        # 回调函数名

@dataclass
class GuidanceTour:
    """引导流程"""
    id: str
    name: str
    description: str
    steps: List[GuidanceStep]
    trigger_event: GuidanceEvent
    conditions: Dict[str, Any]  # 触发条件

@dataclass
class GuidanceContext:
    """引导上下文"""
    user_id: str
    event: GuidanceEvent
    data: Dict[str, Any]
```

### 4.3 事件上下文格式

```javascript
// USER_REGISTERED 上下文
{
  userId: string,
  teams: Array<{ id, name }>
}

// FIRST_FILE_UPLOADED 上下文
{
  fileId: string,
  fileName: string,
  spaceId: string,
  uploadCount: number
}

// QUOTA_WARNING 上下文
{
  spaceId: string,
  spaceName: string,
  quotaUsage: number  // 0.0 - 1.0
}
```

### 4.4 组件间通信事件

```javascript
// 触发工作流引导 Tour
window.dispatchEvent(new CustomEvent('guidance:workflow-tour'))

// 触发笔记本引导 Tour
window.dispatchEvent(new CustomEvent('guidance:notebook-tour'))

// 触发分享对话框
window.dispatchEvent(new CustomEvent('guidance:open-share'))

// 触发协作对话框
window.dispatchEvent(new CustomEvent('guidance:open-collab'))

// 便捷触发函数 (guidanceTrigger.js)
triggerUpload()      // 触发上传引导
triggerTeamJoin()    // 触发加入团队引导
```

### 4.5 引导与生命周期集成

引导引擎与生命周期约束引擎集成，在显示引导前检查操作约束：

```python
def trigger(self, event: GuidanceEvent, context: GuidanceContext):
    tours = self._tours.get(event, [])
    for tour in tours:
        if tour.check_conditions(context.data):
            # 检查生命周期约束
            if self._lifecycle_engine:
                constraint = self._lifecycle_engine.check("show_guidance", context.data)
                if constraint:
                    logger.debug(f"Constraint {constraint.code} prevents guidance")
                    continue
            self._start_tour(tour, context)
```

---

## 六、契约测试

### 6.1 契约测试框架

契约测试确保前后端接口定义与实现保持一致，避免"接口文档与代码脱节"的问题。

**测试框架选型**:
- 后端: `pytest` + `requests`
- 前端: `Jest` + `nock` (接口 Mock)
- E2E: `Playwright`

### 6.2 Lifecycle 契约测试

```python
# tests/contract/test_lifecycle_contract.py

import pytest
from lifecycle_engine import LifecycleEngine

class TestLifecycleContract:
    """前后端 Lifecycle 契约一致性测试"""

    @pytest.fixture
    def engine(self):
        return LifecycleEngine()

    # ========== 契约1: upload_file 约束检查 ==========
    def test_upload_file_requires_membership(self, engine):
        """
        契约: upload_file 必须在 is_member=False 时返回 NOT_SPACE_MEMBER
        前端 lifecycle-interceptor.js 必须与此处一致
        """
        result = engine.check("upload_file", {"is_member": False, "sufficient_quota": True})
        assert result is not None
        assert result.code == "NOT_SPACE_MEMBER"

    def test_upload_file_quota_check(self, engine):
        """
        契约: upload_file 必须在 sufficient_quota=False 时返回 QUOTA_SUFFICIENT
        """
        result = engine.check("upload_file", {"is_member": True, "sufficient_quota": False})
        assert result is not None
        assert result.code == "QUOTA_SUFFICIENT"

    # ========== 契约2: 引导 Action 格式 ==========
    def test_guidance_action_format(self, engine):
        """
        契约: guidance 必须包含 action 和 url 字段
        """
        context = {"team_count": 1}
        try:
            engine.raise_if_violated("delete_pool", context)
        except LifecycleViolation as e:
            assert "action" in e.guidance
            assert "url" in e.guidance

    # ========== 契约3: 边缘 Case 错误码 ==========
    def test_edge_case_pool_teams_migrating(self, engine):
        """
        契约: delete_pool 时 team_migrating_count > 0 返回 POOL_TEAMS_MIGRATING
        """
        result = engine.check("delete_pool", {"team_count": 0, "team_migrating_count": 3})
        assert result is not None
        assert result.code == "POOL_TEAMS_MIGRATING"

    def test_edge_case_quota_reserved(self, engine):
        """
        契约: upload_file 时 quota_reserved > 0 返回 QUOTA_RESERVED
        """
        result = engine.check("upload_file", {
            "is_member": True,
            "sufficient_quota": True,
            "quota_reserved": 1024 * 1024 * 100
        })
        assert result is not None
        assert result.code == "QUOTA_RESERVED"
```

### 6.3 前端契约测试示例

```javascript
// tests/contract/lifecycle-interceptor.spec.js

import { LifecycleInterceptor } from '@/interceptors/LifecycleInterceptor'

describe('LifecycleInterceptor Contract Tests', () => {
  let interceptor

  beforeEach(() => {
    interceptor = new LifecycleInterceptor({ debug: false })
  })

  // ========== 契约1: 约束规则一致性 ==========
  it('should match backend upload_file constraint: is_member required', async () => {
    // 前端约束: is_member 必须为 true
    const result1 = await interceptor.beforeAction('upload_file', {
      isMember: false,
      hasQuota: true
    })
    expect(result1.allowed).toBe(false)
    expect(result1.error.title).toBe('无法上传文件')

    // 与后端 engine.check("upload_file", {"is_member": False}) 一致
  })

  // ========== 契约2: guidance 格式一致性 ==========
  it('should match backend guidance format', async () => {
    const result = await interceptor.beforeAction('upload_file', {
      isMember: false,
      hasQuota: true
    })

    // 后端 guidance 格式: { action: string, url: string }
    expect(result.guidance).toEqual(expect.objectContaining({
      action: expect.any(String),
      url: expect.stringMatching(/^\//)  // 相对路径或绝对路径
    }))
  })

  // ========== 契约3: 边缘 case 一致性 ==========
  it('should handle quota_reserved edge case same as backend', async () => {
    const result = await interceptor.beforeAction('upload_file', {
      isMember: true,
      hasQuota: true,
      quotaReserved: 1024 * 1024 * 100,  // 100MB reserved
      canOverride: false
    })

    // 前端返回格式必须与后端一致
    expect(result.allowed).toBe(false)
    expect(result.error.title).toBe('无法上传文件')  // 或 "配额被占用"
  })
})
```

### 6.4 WebSocket 契约测试示例

```javascript
describe('WebSocket Messages Contract', () => {
  it('should receive analytics_update with correct structure', (done) => {
    const ws = new WebSocket('ws://localhost:8080/ws/admin/analytics?token=<token>')

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      expect(data).toHaveProperty('type')
      expect(data).toHaveProperty('timestamp')
      if (data.type === 'analytics_update') {
        expect(data.data).toHaveProperty('overview')
        expect(data.data).toHaveProperty('alerts')
      }
      done()
    }
  })
})
```

### 6.5 契约测试执行

```bash
# 运行所有契约测试
pytest tests/contract/ -v

# 运行生命周期契约测试
pytest tests/contract/test_lifecycle_contract.py -v

# 运行前端契约测试
npm run test -- --testPathPattern="contract"
```

---

## 七、版本历史

| 版本 | 日期 | 修改内容 |
|------|------|---------|
| 1.0 | 2026-05-02 | 初始版本，定义 REST API、WebSocket、EventBus、Guidance 契约 |
| 1.1 | 2026-05-02 | 补充第五节"契约测试" |
| 1.2 | 2026-05-05 | 修正错误码格式（移除 LIFECYCLE_ 前缀），更新 guidance 格式与 lifecycle_engine.py 一致 |