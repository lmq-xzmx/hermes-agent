# 接口契约文档 (Interface Contract)

> **版本**: 1.2
> **更新日期**: 2026-05-05
> **目的**: 定义前后端、WebSocket、EventBus 的接口契约，确保集成一致性
> **更新说明 v1.2**: 修正错误码格式与 lifecycle_engine.py 一致（移除 LIFECYCLE_ 前缀），更新 guidance 格式

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

### 1.2 Lifecycle API

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

### 2.2 客户端发送

**Ping**
```json
{
  "type": "ping"
}
```

### 2.3 服务器推送

**Analytics Update** (每30秒)
```json
{
  "type": "analytics_update",
  "data": {
    "overview": { ... },
    "alerts": [ ... ]
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

### 4.2 事件上下文格式

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

### 4.3 组件间通信事件

```javascript
// 触发工作流引导 Tour
window.dispatchEvent(new CustomEvent('guidance:workflow-tour'))

// 触发笔记本引导 Tour
window.dispatchEvent(new CustomEvent('guidance:notebook-tour'))

// 触发分享对话框
window.dispatchEvent(new CustomEvent('guidance:open-share'))

// 触发协作对话框
window.dispatchEvent(new CustomEvent('guidance:open-collab'))
```

---

## 五、契约测试

### 5.1 契约测试框架

契约测试确保前后端接口定义与实现保持一致，避免"接口文档与代码脱节"的问题。

**测试框架选型**:
- 后端: `pytest` + `requests`
- 前端: `Jest` + `nock` (接口 Mock)
- E2E: `Playwright`

### 5.2 Lifecycle 契约测试

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

### 5.3 前端契约测试示例

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

### 5.4 WebSocket 契约测试示例

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

### 5.5 契约测试执行

```bash
# 运行所有契约测试
pytest tests/contract/ -v

# 运行生命周期契约测试
pytest tests/contract/test_lifecycle_contract.py -v

# 运行前端契约测试
npm run test -- --testPathPattern="contract"
```

---

## 六、版本历史

| 版本 | 日期 | 修改内容 |
|------|------|---------|
| 1.0 | 2026-05-02 | 初始版本，定义 REST API、WebSocket、EventBus、Guidance 契约 |
| 1.1 | 2026-05-02 | 补充第五节"契约测试" |
| 1.2 | 2026-05-05 | 修正错误码格式（移除 LIFECYCLE_ 前缀），更新 guidance 格式与 lifecycle_engine.py 一致 |