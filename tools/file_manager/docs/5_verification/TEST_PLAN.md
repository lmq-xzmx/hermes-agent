# 测试计划与验证方案

> **版本**: 1.1
> **更新日期**: 2026-05-05
> **基于**: Vue 3 + Pinia + Tauri 架构
> **补充说明**: 更新为 Vue 3 + Tauri 测试策略

---

## 一、测试现状分析

### 1.1 当前覆盖率

```
┌─────────────────────────────────────────────────────────────────┐
│                      测试覆盖率现状                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  单元测试 (L2 Domain层):                                        │
│  ├── 后端 (pytest):                                            │
│  │   ├── lifecycle_engine.py: ~85% ✅                          │
│  │   └── team_service.py:     ~60% ⚠️                          │
│  └── 前端 (Vitest + @vue/test-utils):                          │
│      └── guidanceStore.js:    ~30% ⚠️                          │
│                                                                 │
│  集成测试 (L1 Infrastructure):                                  │
│  ├── API 端点:              ~30% ❌                             │
│  └── WebSocket:               0% ❌                             │
│                                                                 │
│  E2E 测试 (用户旅程):        ~20% ❌                             │
│                                                                 │
│  问题: Vue 3 组件测试覆盖不足，E2E 尚未全面覆盖                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 测试技术栈

| 层级 | 工具 | 说明 |
|------|------|------|
| 前端单元测试 | Vitest + @vue/test-utils | Vue 3 组件测试 |
| 前端 E2E | Playwright | 浏览器自动化 |
| 后端单元测试 | pytest + pytest-cov | Python 单元测试 |
| 后端集成测试 | pytest + requests | API 测试 |
| Tauri 测试 | Playwright (WebView) | 桌面应用测试 |

---

## 二、测试金字塔实施

### 2.1 L1: 单元测试 (Domain Layer)

**目标**: >80% 覆盖率
**工具**: Vitest (前端) / pytest (后端)
**负责人**: A4 (前端), B1/B2 (后端)

#### 2.1.1 前端单元测试 (Vue 3 + Pinia)

```javascript
// tests/unit/guidanceStore.test.js
import { setActivePinia, createPinia } from 'pinia'
import { describe, it, expect, beforeEach } from 'vitest'
import { useGuidanceStore } from '@/stores/guidanceStore'

describe('useGuidanceStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('trigger: should show guidance modal for registered event', () => {
    const store = useGuidanceStore()
    store.trigger('user_registered', { teams: [] })

    expect(store.modalVisible).toBe(true)
    expect(store.currentEventName).toBe('user_registered')
  })

  it('trigger: should not show if event is dismissed', () => {
    const store = useGuidanceStore()
    store.dismiss('user_registered')
    store.trigger('user_registered', { teams: [] })

    expect(store.modalVisible).toBe(false)
  })

  it('dismiss: should persist to localStorage', () => {
    const store = useGuidanceStore()
    store.dismiss('user_registered')

    expect(store.isDismissed('user_registered')).toBe(true)
  })

  it('updateContext: should merge updates correctly', () => {
    const store = useGuidanceStore()
    store.updateContext({ teams: ['team1'], uploadCount: 1 })

    expect(store.context.teams).toEqual(['team1'])
    expect(store.context.uploadCount).toBe(1)
  })
})
```

```javascript
// tests/unit/components/WorkflowTourGuide.test.js
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import WorkflowTourGuide from '@/components/guidance/WorkflowTourGuide.vue'

describe('WorkflowTourGuide.vue', () => {
  it('should render tour steps correctly', () => {
    const wrapper = mount(WorkflowTourGuide, {
      props: {
        visible: true,
        steps: [
          { target: '#step1', content: 'Step 1', position: 'bottom' }
        ]
      }
    })

    expect(wrapper.find('.tour-step').exists()).toBe(true)
  })
})
```

#### 2.1.2 后端单元测试

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

### 2.2 L2: 集成测试 (API Layer)

**目标**: >60% 覆盖率
**工具**: pytest + requests
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
        """验证团队按存储池查询"""
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
        """WebSocket 连接需要 admin 角色"""
        with pytest.raises(websocket.WebSocketDisconnect) as exc:
            with websocket.connect(f'ws://localhost/ws/admin/analytics?token={self.user_token}'):
                pass
        # 期望 4001 Unauthorized
        assert exc.value.code == 4001

    def test_websocket_ping_pong(self):
        """WebSocket ping-pong 心跳"""
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
    await page.goto('/spaces/team1/workflows')
    await page.click('[data-tour="workflow-create-btn"]')

    // 验证 Tour 弹窗出现
    await page.waitForSelector('.guidance-modal')
    const modal = await page.locator('.guidance-modal')
    expect(await modal.textContent()).toContain('工作流')
  })

  test('M3: Guidance state persists after dismiss', async ({ page }) => {
    await page.goto('/spaces/team1/workflows')
    await page.click('[data-tour="workflow-create-btn"]')
    await page.waitForSelector('.guidance-modal')
    await page.click('.guidance-close')

    // 刷新页面
    await page.reload()
    await page.goto('/spaces/team1/workflows')

    // 验证引导不再出现
    await page.click('[data-tour="workflow-create-btn"]')
    await page.waitForTimeout(500)
    const modal = page.locator('.guidance-modal')
    await expect(modal).not.toBeVisible()
  })
})
```

#### 2.3.2 Tauri 桌面应用测试

```typescript
// e2e/tauri-app.spec.ts
test.describe('Tauri Desktop App', () => {
  test('should open main window', async ({ page }) => {
    // Tauri 使用 WebView，直接测试 Vue SPA
    await page.goto('http://localhost:1420/')
    await page.waitForSelector('#app')

    expect(await page.title()).toBe('Hermes File Manager')
  })

  test('should display guidance modal on first login', async ({ page }) => {
    await page.goto('http://localhost:1420/')
    await page.waitForSelector('#app')

    // 模拟登录后触发引导
    await page.evaluate(() => {
      window.__vueGuidance?.trigger('user_registered', { teams: [] })
    })

    await page.waitForSelector('.guidance-modal')
    expect(await page.locator('.guidance-title').textContent()).toContain('欢迎')
  })
})
```

---

## 三、TDD 流程实施

### 3.1 Red-Green-Refactor 循环

```
┌─────────────────────────────────────────────────────────────────┐
│                    TDD 开发流程                                   │
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
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
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
        uses: codecov/codecov-action@v4

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests (Vitest)
        run: pnpm test

      - name: Run E2E tests (Playwright)
        run: npm run test:e2e
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

### 5.1 前端 Vue 3 组件测试

| TC ID | 测试用例 | 状态 |
|-------|---------|------|
| TC-VUE-001 | guidanceStore 事件触发 | ⚠️ 部分通过 |
| TC-VUE-002 | guidanceStore 状态持久化 | ⚠️ 部分通过 |
| TC-VUE-003 | WorkflowTourGuide 组件渲染 | ❌ 待开发 |
| TC-VUE-004 | NotebookTourGuide 组件渲染 | ❌ 待开发 |
| TC-VUE-005 | 引导弹窗交互 | ⚠️ 部分通过 |

### 5.2 M1: Admin 控制台

| TC ID | 测试用例 | RTM 追踪 | 状态 |
|-------|---------|---------|------|
| TC-M1-001 | WebSocket 连接成功 | REQ-M1-001 | ~~~WebSocket 连接成功~~~ ✅已通过 |
| TC-M1-002 | AdminOverview 数据正确显示 | REQ-M1-002 | ~~~AdminOverview 数据正确显示~~~ ✅已通过 |
| TC-M1-003 | ECharts 暗色主题正常 | REQ-M1-003 | ~~~ECharts 暗色主题正常~~~ ✅已通过 |
| TC-M1-004 | WebSocket 重连机制 | REQ-M1-001 | 🔄 E2E 测试已创建 (websocket.spec.js) |
| TC-M1-005 | WebSocket 消息格式正确 | REQ-M1-001 | 🔄 E2E 测试已创建 (websocket.spec.js) |

### 5.3 M2: 生命周期约束

| TC ID | 测试用例 | RTM 追踪 | 状态 |
|-------|---------|---------|------|
| TC-M2-001 | 删除有团队的存储池失败 | REQ-M2-005 | ~~~删除有团队的存储池失败~~~ ✅已通过 |
| TC-M2-002 | 非成员上传文件被拦截 | REQ-M2-002 | ~~~非成员上传文件被拦截~~~ ✅已通过 |
| TC-M2-003 | 前端拦截器显示引导弹窗 | REQ-M2-015 | ~~~前端拦截器显示引导弹窗~~~ ✅已通过 |
| TC-M2-004 | 并发上传配额锁定 | REQ-M2-017 | ~~~并发上传配额锁定~~~ ✅ 已完成 - SELECT FOR UPDATE + 预留配额 |
| TC-M2-005 | 配额超卖防护 SELECT FOR UPDATE | REQ-M2-017 | ~~~配额超卖防护 SELECT FOR UPDATE~~~ ✅ 已完成 - with_for_update() 原子操作 |
| TC-M2-006 | 并发邀请唯一索引防重 | REQ-M2-018 | ~~~并发邀请唯一索引防重~~~ ✅已通过 |
| TC-M2-007 | 重复邀请返回错误 | REQ-M2-018 | ~~~重复邀请返回错误~~~ ✅已通过 |

### 5.4 M3: 新手引导

| TC ID | 测试用例 | RTM 追踪 | 状态 |
|-------|---------|---------|------|
| TC-M3-001 | 文件上传触发引导事件 | REQ-M3-001 | ~~~文件上传触发引导事件~~~ ✅ 已完成 - handleFileUpload 中集成引导触发 |
| TC-M3-002 | 引导状态 localStorage 持久化 | REQ-M3-002 | ~~~引导状态 localStorage 持久化~~~ ✅已通过 |
| TC-M3-003 | Workflow Tour 3 节点展示 | REQ-M3-003 | ~~~Workflow Tour 3 节点展示~~~ ✅已通过 |
| TC-M3-004 | Notebook Tour 4 节点展示 | REQ-M3-004 | ~~~Notebook Tour 4 节点展示~~~ ✅已通过 |
| TC-M3-005 | TourGuide 组件复用正常 | REQ-M3-005 | ~~~TourGuide 组件复用正常~~~ ✅已通过 |
| TC-M3-006 | 触发点正确绑定到 DOM | REQ-M3-001 | ⚠️ 部分验证 |

### 5.5 UI-6: 框选功能

| TC ID | 测试用例 | 状态 | 验证文件 |
|-------|---------|------|----------|
| TC-UI6-001 | 鼠标拖拽创建选框，选中多个文件 | ✅ 已完成 | useDragSelection.js |
| TC-UI6-002 | 选框与点击文件行不冲突 | ✅ 已完成 | useDragSelection.js:68 |
| TC-UI6-003 | 选框支持键盘 Shift 多选 | ✅ 已完成 | useDragSelection.js:79 |
| TC-UI6-004 | 点击空白处清除选区 | ✅ 已完成 | useDragSelection.js:124 |

### 5.6 UI-9: 拖拽移动功能

| TC ID | 测试用例 | 状态 | 验证文件 |
|-------|---------|------|----------|
| TC-UI9-001 | 拖拽文件到目标文件夹，高亮显示可释放区域 | 🔄 需补充 | dragMove.js (若有) |
| TC-UI9-002 | 拖拽过程中按 Escape 取消 | 🔄 需补充 | dragMove.js (若有) |
| TC-UI9-003 | 拖拽到无效区域自动弹回 | 🔄 需补充 | dragMove.js (若有) |
| TC-UI9-004 | 批量拖拽多个文件 | 🔄 需补充 | dragMove.js (若有) |
| TC-UI9-005 | 拖拽权限检查（非所有者不可移动） | 🔄 需补充 | dragMove.js (若有) |

---

## 六、执行计划

### 6.1 Sprint 1 (1-2周): 测试骨架完善

| 任务 | 负责人 | 产出 |
|------|--------|------|
| 补充 Vue 3 组件测试 (Vitest) | A4 | guidanceStore.test.js |
| 补充 M3 引导流程 E2E | T2 | guidance-flow.spec.ts |
| WebSocket 测试环境 | T1 | test_websocket.py |

### 6.2 Sprint 2 (3-4周): 覆盖度提升

| 任务 | 负责人 | 产出 |
|------|--------|------|
| Admin Dashboard E2E | T2 | admin-dashboard.spec.ts |
| 配额预留测试补充 | B1, T1 | TC-M2-004, TC-M2-005 |
| Tauri 桌面应用 E2E | T2 | tauri-app.spec.ts |

### 6.3 Sprint 3 (5-6周): 完善与优化

| 任务 | 负责人 | 产出 |
|------|--------|------|
| 覆盖率达标验证 | T1 | coverage > 80% |
| RTM 测试用例更新 | PM | RTM.md 更新 |
| 性能测试补充 | T1 | 响应时间 < 500ms |

---

## 七、Vitest 配置

```javascript
// vitest.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.{test,spec}.{js,ts}'],
    setupFiles: ['./tests/setup.ts']
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
```

---

## 八、Playwright 配置

```javascript
// playwright.config.js
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
})
```

---

## 九、相关文档

- [RTM.md](../7_tracking/RTM.md) - 需求追踪矩阵
- [RTM_REQUIREMENTS_TRACEABILITY.md](../7_tracking/RTM_REQUIREMENTS_TRACEABILITY.md) - 需求可追溯性
- [TOP_DOWN_DEVELOPMENT.md](../1_architecture/TOP_DOWN_DEVELOPMENT.md) - 开发方法论
- [GUIDANCE_INTEGRATION.md](./GUIDANCE_INTEGRATION.md) - 引导系统集成