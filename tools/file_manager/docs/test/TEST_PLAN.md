# 测试计划与验证方案

> **版本**: 1.0
> **更新日期**: 2026-05-02
> **基于**: TOP_DOWN_DEVELOPMENT.md 测试金字塔
> **补充说明**: 基于自顶向下审视，发现测试覆盖严重不足，需系统性补充

---

## 一、测试现状分析

### 1.1 当前覆盖率

```
┌─────────────────────────────────────────────────────────────────┐
│                      测试覆盖率现状                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  单元测试 (L2 Domain层):                                        │
│  ├── lifecycle_engine.py: ~85% ✅                               │
│  ├── team_service.py:     ~60% ⚠️                              │
│  └── guidance_engine.js:   ~40% ❌                              │
│                                                                 │
│  集成测试 (L1 Infrastructure):                                  │
│  ├── API 端点:              ~30% ❌                             │
│  └── WebSocket:               0% ❌                             │
│                                                                 │
│  E2E 测试 (用户旅程):        ~20% ❌                             │
│                                                                 │
│  问题: P1/P2/P3 增量阶段均无测试骨架，导致集成时问题频发           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 待验证项目 (RTM 追踪)

| RTM ID | 需求描述 | 测试用例 | 状态 | 优先级 |
|--------|---------|---------|------|--------|
| REQ-M1-001 | WebSocket连接 | TC-M1-001 | ❌待验证 | P1 |
| REQ-M3-001 | 触发点连接 | TC-M3-001 | ❌待验证 | P1 |
| REQ-M2-017 | 配额超卖防护 | TC-M2-004, TC-M2-005 | ❌待开发 | P0 |
| REQ-M2-018 | 并发邀请防护 | TC-M2-006, TC-M2-007 | ❌待验证 | P0 |

---

## 二、测试金字塔实施

### 2.1 L1: 单元测试 (Domain Layer)

**目标**: >80% 覆盖率
**工具**: pytest + pytest-cov
**负责人**: B1, B2 (后端), A4 (前端)

#### 2.1.1 后端单元测试

```python
# tests/unit/test_lifecycle_engine.py
class TestLifecycleEngine:
    """生命周期约束引擎单元测试"""

    def test_raise_if_violated_quota_exceeded(self):
        """REQ-M2-001: 配额超限应抛出异常"""
        engine = get_lifecycle_engine()
        context = {"space_id": "space1", "used_bytes": 100, "max_bytes": 50}
        with pytest.raises(LifecycleViolation) as exc:
            engine.raise_if_violated("check_quota", context)
        assert exc.value.code == "SPACE_QUOTA_EXCEEDED"

    def test_raise_if_violated_pool_in_use(self):
        """REQ-M2-005: 存储池有团队时应禁止删除"""
        engine = get_lifecycle_engine()
        context = {"pool_id": "pool1", "team_count": 3}
        with pytest.raises(LifecycleViolation) as exc:
            engine.raise_if_violated("delete_pool", context)
        assert exc.value.code == "STORAGE_POOL_IN_USE"

    def test_edge_case_pool_migrating(self):
        """REQ-M2-011: POOL_MIGRATING 边缘case"""
        engine = get_lifecycle_engine()
        context = {"pool_id": "pool1", "team_count": 0, "team_migrating_count": 2}
        with pytest.raises(LifecycleViolation) as exc:
            engine.raise_if_violated("delete_pool", context)
        assert exc.value.code == "POOL_TEAMS_MIGRATING"
```

```python
# tests/unit/test_team_service.py
class TestTeamService:
    """TeamService 业务逻辑单元测试"""

    def test_create_team_requires_available_pool(self):
        """REQ-M2-003: 无可用池禁止创建团队"""
        with pytest.raises(LifecycleViolation) as exc:
            svc.create_team(name="Test", owner_id="u1", storage_pool_id="pool1")
        assert exc.value.code == "NO_AVAILABLE_POOL"

    def test_delete_pool_blocks_when_teams_exist(self):
        """REQ-M2-005: 存储池有团队时禁止删除"""
        svc = TeamService(db_factory)
        with pytest.raises(LifecycleViolation):
            svc.delete_pool(pool_id="pool_with_teams")
```

#### 2.1.2 前端单元测试

```javascript
// tests/unit/guidanceEngine.test.js
describe('GuidanceEngine', () => {
  test('trigger: should fire event for registered guidance', () => {
    const engine = new GuidanceEngine()
    engine.register({
      USER_REGISTERED: {
        title: 'Welcome',
        message: 'Join a team',
        condition: (ctx) => ctx.teams?.length === 0
      }
    })
    const result = engine.trigger('USER_REGISTERED', { teams: [] })
    expect(result).toBe(true)
  })

  test('dismiss: should persist to localStorage', () => {
    const engine = new GuidanceEngine()
    engine.dismiss('USER_REGISTERED')
    expect(engine.isDismissed('USER_REGISTERED')).toBe(true)
  })
})
```

### 2.2 L2: 集成测试 (API Layer)

**目标**: >60% 覆盖率
**工具**: pytest + requests + Testcontainers
**负责人**: T1 (测试)

#### 2.2.1 API 端点集成测试

```python
# tests/integration/test_admin_api.py
class TestAdminAnalyticsAPI:
    """Admin Analytics API 集成测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = TestClient(app)

    def test_storage_pools_endpoint(self):
        """验证存储池列表 API"""
        response = self.client.get(
            '/api/v1/admin/analytics/storage-pools',
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'pools' in data
        assert len(data['pools']) > 0

    def test_teams_by_pool_endpoint(self):
        """REQ-M3-001 依赖: 验证团队按存储池查询"""
        response = self.client.get(
            f'/api/v1/admin/analytics/teams-by-pool/{self.pool_id}',
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'teams' in data
        assert data['pool_id'] == self.pool_id
```

#### 2.2.2 WebSocket 集成测试

```python
# tests/integration/test_websocket.py
class TestWebSocketAnalytics:
    """WebSocket 实时推送集成测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = TestClient(app)

    def test_websocket_connection_requires_admin(self):
        """REQ-M1-001: WebSocket 连接需要 admin 角色"""
        with pytest.raises(websocket.WebSocketDisconnect) as exc:
            with websocket.connect(f'ws://localhost/ws/admin/analytics?token={self.user_token}'):
                pass
        # 期望 4001 Unauthorized
        assert exc.value.code == 4001

    def test_websocket_ping_pong(self):
        """REQ-M1-001: WebSocket ping-pong 心跳"""
        with websocket.connect(f'ws://localhost/ws/admin/analytics?token={self.admin_token}') as ws:
            ws.send_json({'type': 'ping'})
            response = ws.receive_json()
            assert response['type'] == 'pong'
```

### 2.3 L3: E2E 测试 (用户旅程)

**目标**: 关键路径全覆盖
**工具**: Playwright
**负责人**: T2 (E2E)

#### 2.3.1 关键用户旅程

```typescript
// e2e/user-journeys.spec.ts

test.describe('Admin Dashboard Journey', () => {
  test('M1: Admin can view real-time analytics', async ({ page }) => {
    // REQ-M1-001: WebSocket 实时数据验证
    await page.goto('/admin/dashboard')
    await page.waitForSelector('.admin-overview')

    // 等待 WebSocket 连接建立
    await page.waitForFunction(() => window.wsAdminConnected === true)

    // 验证数据实时更新
    const initialValue = await page.locator('.stat-value').first().textContent()
    // ... trigger some action ...
    await page.waitForTimeout(1000)
    const newValue = await page.locator('.stat-value').first().textContent()
    expect(newValue).not.toBe(initialValue)
  })
})

test.describe('Guidance Tour Journey', () => {
  test('M3: Workflow tour triggers on workflow creation', async ({ page }) => {
    // REQ-M3-001: 触发点连接验证
    await page.goto('/spaces/team1/workflows')
    await page.click('[data-tour="workflow-create-btn"]')

    // 验证 Tour 弹窗出现
    await page.waitForSelector('.tour-tooltip')
    const tooltip = await page.locator('.tour-tooltip')
    expect(await tooltip.textContent()).toContain('新建工作流')
  })

  test('M3: Guidance state persists after dismiss', async ({ page }) => {
    // REQ-M3-002: 引导状态持久化
    await page.goto('/spaces/team1/workflows')
    await page.click('[data-tour="workflow-create-btn"]')
    await page.waitForSelector('.tour-tooltip')
    await page.click('.tour-close')

    // 刷新页面
    await page.reload()
    await page.goto('/spaces/team1/workflows')

    // 验证引导不再出现
    await page.click('[data-tour="workflow-create-btn"]')
    await page.waitForTimeout(500)
    const tooltip = page.locator('.tour-tooltip')
    await expect(tooltip).not.toBeVisible()
  })
})
```

---

## 三、TDD 流程实施

### 3.1 Red-Green-Refactor 循环

```
┌─────────────────────────────────────────────────────────────────┐
│                    TDD 开发流程                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Red: 编写一个失败的测试用例                                  │
│     └── test_delete_pool_with_teams_should_fail()               │
│         → AssertionError: 期望抛出 LifecycleViolation            │
│                                                                 │
│  2. Green: 编写最少量代码让测试通过                              │
│     └── 在 delete_pool() 中添加 team_count 检查                  │
│         → 测试通过                                              │
│                                                                 │
│  3. Refactor: 重构代码，消除重复                               │
│     └── 提取 team_count 检查到 lifecycle_engine.raise_if_violated() │
│         → 测试仍然通过                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 每日 TDD 小循环

```
Morning (30min):
├── 选择一个任务 (从 Sprint Backlog)
├── 编写失败的测试 (Red)
├── 实现代码让测试通过 (Green)
└── 重构 (Refactor)

Evening (30min):
├── 代码审查
├── 更新 RTM 测试用例状态
└── 提交 PR
```

---

## 四、CI/CD 质量门禁

### 4.1 Pipeline 配置

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest pytest-cov pytest-asyncio
          pip install -r requirements.txt

      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=. --cov-report=xml

      - name: Run integration tests
        run: |
          pytest tests/integration/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npx playwright test
```

### 4.2 质量门禁标准

| 检查项 | 阈值 | 失败动作 |
|--------|------|---------|
| 单元测试覆盖率 | >80% | Block PR |
| 集成测试通过率 | 100% | Block PR |
| E2E 测试通过率 | 100% | Block PR |
| 代码重复率 | <5% | Warning |
| 安全扫描 | 0 高危 | Block PR |

---

## 五、测试用例清单

### 5.1 M1: Admin 控制台

| TC ID | 测试用例 | RTM 追踪 | 状态 |
|-------|---------|---------|------|
| TC-M1-001 | WebSocket 连接成功 | REQ-M1-001 | ❌待验证 |
| TC-M1-002 | AdminOverview 数据正确显示 | REQ-M1-002 | ✅已通过 |
| TC-M1-003 | ECharts 暗色主题正常 | REQ-M1-003 | ✅已通过 |
| TC-M1-004 | WebSocket 重连机制 | REQ-M1-001 | ❌待验证 |
| TC-M1-005 | WebSocket 消息格式正确 | REQ-M1-001 | ❌待验证 |

### 5.2 M2: 生命周期约束

| TC ID | 测试用例 | RTM 追踪 | 状态 |
|-------|---------|---------|------|
| TC-M2-001 | 删除有团队的存储池失败 | REQ-M2-005 | ✅已通过 |
| TC-M2-002 | 非成员上传文件被拦截 | REQ-M2-002 | ✅已通过 |
| TC-M2-003 | 前端拦截器显示引导弹窗 | REQ-M2-015 | ✅已通过 |
| TC-M2-004 | 并发上传配额锁定 | REQ-M2-017 | ❌待开发 |
| TC-M2-005 | 配额超卖防护 SELECT FOR UPDATE | REQ-M2-017 | ❌待开发 |
| TC-M2-006 | 并发邀请唯一索引防重 | REQ-M2-018 | ✅已通过 |
| TC-M2-007 | 重复邀请返回错误 | REQ-M2-018 | ✅已通过 |

### 5.3 M3: 新手引导

| TC ID | 测试用例 | RTM 追踪 | 状态 |
|-------|---------|---------|------|
| TC-M3-001 | 文件上传触发引导事件 | REQ-M3-001 | ❌待验证 |
| TC-M3-002 | 引导状态 localStorage 持久化 | REQ-M3-002 | ✅已通过 |
| TC-M3-003 | Workflow Tour 3 节点展示 | REQ-M3-003 | ✅已通过 |
| TC-M3-004 | Notebook Tour 4 节点展示 | REQ-M3-004 | ✅已通过 |
| TC-M3-005 | TourGuide 组件复用正常 | REQ-M3-005 | ✅已通过 |
| TC-M3-006 | 触发点正确绑定到 DOM | REQ-M3-001 | ❌待验证 |

---

## 六、执行计划

### 6.1 Sprint 1 (1-2周): 测试骨架

| 任务 | 负责人 | 产出 |
|------|--------|------|
| 搭建 pytest 骨架 | T1 | tests/unit/, tests/integration/ |
| 配置 pytest-cov | T1 | coverage.yml |
| 补充 M2 单元测试 | B1 | test_lifecycle_engine.py |
| 补充 M2 集成测试 | T1 | test_admin_api.py |
| WebSocket 测试环境 | T1 | test_websocket.py |

### 6.2 Sprint 2 (3-4周): E2E 补充

| 任务 | 负责人 | 产出 |
|------|--------|------|
| 搭建 Playwright 骨架 | T2 | e2e/ |
| Admin Dashboard E2E | T2 | admin-dashboard.spec.ts |
| Guidance Tour E2E | T2 | guidance-flow.spec.ts |
| 触发点集成验证 | A2, T2 | TC-M3-001, TC-M3-006 |
| WebSocket E2E | A3, T2 | websocket.spec.ts |

### 6.3 Sprint 3 (5-6周): 完善与优化

| 任务 | 负责人 | 产出 |
|------|--------|------|
| REQ-M2-017 实现 | B1 | 配额超卖防护 |
| 补充配额超卖测试 | T1 | TC-M2-004, TC-M2-005 |
| RTM 测试用例更新 | PM | RTM.md 更新 |
| 覆盖率达标验证 | T1 | coverage > 80% |

---

## 七、相关文档

- [RTM.md](./RTM.md) - 需求追踪矩阵
- [TOP_DOWN_DEVELOPMENT.md](./TOP_DOWN_DEVELOPMENT.md) - 开发方法论
- [IMPLEMENTATION_PLAN_V2.md](./IMPLEMENTATION_PLAN_V2.md) - 实施计划
