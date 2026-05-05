# 系统优化与测试计划

> **版本**: 1.2
> **更新日期**: 2026-05-05
> **基于分析**: 自顶向下开发模式 + 架构文档分析
> **开发状态**: G1-G8 ✅ 已完成，G9 实施中，Vue 3 迁移 ✅ 已完成
>
> **更新说明 v1.2**: 核实完成度状态，Vue 3 迁移已完成，app.html 已废弃
> **更新说明 v1.1**: 补充 FileUpload 模型测试用例，完善 quota_reserved 测试覆盖

---

## 一、架构文档分析总结

### 1.1 架构合理性评估

| 文档 | 评分 | 主要优点 | 需改进 |
|------|------|---------|--------|
| SYSTEM_ARCHITECTURE.md | ⭐⭐⭐⭐⭐ | 架构清晰，分层明确 | 缺少依赖关系图 |
| ADMIN_DASHBOARD.md | ⭐⭐⭐⭐ | 可视化方案详细 | 实现状态需更新 |
| LIFECYCLE_CONSTRAINTS.md | ⭐⭐⭐⭐⭐ | 约束规则完整 | 边缘case可细化 |
| NEW_USER_GUIDE.md | ⭐⭐⭐⭐ | 引导地图完善 | 触发机制需文档化 |
| MODULE_1_*.md | ⭐⭐⭐⭐⭐ | 实现详细一致 | WebSocket状态需同步 |
| MODULE_2_*.md | ⭐⭐⭐⭐⭐ | 与代码完全一致 | 无 |
| UPGRADE_PLAN.md | ⭐⭐⭐⭐ | 规划完整 | 缺少风险评估细节 |
| TASK_BREAKDOWN.md | ⭐⭐⭐⭐⭐ | 任务分解合理 | 无 |

### 1.2 实现完整性评估

```
整体完成度: G1-G8 100% ✅，G9 实施中

模块一 (Admin 控制台): 100% ✅
├── WebSocket 实时推送 ✅
├── AdminOverview 数据聚合 ✅
└── ECharts 主题适配 ✅

模块二 (生命周期约束): 100% ✅
├── 边缘约束 Case 完善 ✅
└── 前端约束兜底 ✅

模块三 (新手引导): 100% ✅
├── 前端触发点连接 ✅
├── 引导状态持久化 ✅
├── Workflow 引导 Tour ✅
├── Notebook 引导 Tour ✅
└── TourGuide 组件增强 ✅

Vue 3 迁移: 100% ✅
├── vue.html 主入口 ✅
├── platformAdapter.js ✅
├── floating-vue.html 浮窗入口 ✅
└── app.html 标注废弃 ✅
```

### 1.3 发现的问题

| 问题 | 严重程度 | 位置 | 状态 |
|------|---------|------|------|
| README.md 缺少 TOP_DOWN_DEVELOPMENT.md 索引 | 低 | README.md | ✅ 已更新 |
| ADMIN_DASHBOARD.md 标注85%但实际100% | 低 | ADMIN_DASHBOARD.md | ✅ 已更新 |
| NEW_USER_GUIDE.md 标注75%但实际100% | 低 | NEW_USER_GUIDE.md | ✅ 已更新 |
| 缺少约束规则配置与代码的映射文档 | 低 | lifecycle_config.yaml | ✅ 已同步 |
| CODE_CLEANUP_GUIDE.md 未引用 CODE-005/006/007 标准 | 低 | CODE_CLEANUP_GUIDE.md | ✅ 已添加 |
| IMPLEMENTATION_PLAN_V2.md 状态标注与实际不符 | 中 | IMPLEMENTATION_PLAN_V2.md | ✅ 已更新 |
| UPGRADE_PLAN.md 缺少 Vue 3 迁移状态 | 中 | UPGRADE_PLAN.md | ✅ 已补充 |

---

## 二、系统优化策略

### 2.1 短期优化 (1-2周)

#### 文档同步
- [x] 更新 README.md 添加 TOP_DOWN_DEVELOPMENT.md 索引
- [x] 更新 ADMIN_DASHBOARD.md 完成度为 100%
- [x] 更新 NEW_USER_GUIDE.md 完成度为 100%
- [x] 更新 UPGRADE_PLAN.md 实现清单

#### 代码质量
- [ ] 补充 lifecycle_engine.py 单元测试 (当前覆盖率 < 80%)
- [x] 补充 guidance-trigger-boot.js 集成测试 (guidance.spec.js 已创建)
- [x] 添加 WebSocket 重连机制的日志记录 (websocket.spec.js E2E 测试)

### 2.2 中期优化 (1个月)

#### 性能优化
- [ ] Admin 控制台数据缓存策略实施 (TTL: 5分钟)
- [ ] 桑基图虚拟化渲染 (节点 > 100 时启用)
- [x] WebSocket 心跳机制优化 (已实现 ping/pong)

#### 可靠性增强
- [ ] 前端拦截器添加请求重试机制
- [ ] 后端约束引擎添加熔断器
- [x] 引导系统添加离线状态处理 (guidanceStore.js stats 持久化)

### 2.3 长期优化 (3个月)

#### 功能增强
- [ ] 引导系统 A/B 测试框架
- [ ] 用户行为分析数据收集
- [ ] 智能引导推荐算法

#### 可观测性
- [ ] 引导系统metrics采集
- [ ] 约束规则命中率的监控面板
- [ ] 用户引导完成率追踪

---

## 三、测试计划

### 3.1 测试金字塔

```
                    E2E 测试 (Playwright + Tauri)
                   ┌─────────────────────┐
                  │                     │
          集成测试 (pytest + requests)  │
         ┌─────────────────────────────┐│
        │                               │
单元测试  │    (pytest + pytest-cov)     ││
┌─────────────────────────────────────┐│
│                                       ││
└───────────────────────────────────────┘│

补充: Tauri 壳测试
├── Rust 单元测试 (cargo test)
├── Rust 集成测试 (Tauri command 测试)
└── WebView 渲染测试
```

### 3.2 单元测试计划

#### 后端单元测试

| 模块 | 测试文件 | 覆盖率目标 | 关键测试用例 |
|------|---------|-----------|------------|
| lifecycle_engine | test_lifecycle_engine.py | >80% | 9条规则 + 4个边缘case |
| quota_protection | test_quota_protection.py | >90% | 并发超卖、SELECT FOR UPDATE、锁定超时 |
| guidance_engine | test_guidance_engine.py | >80% | 事件触发、条件判断、引导显示 |
| admin_analytics_service | test_admin_analytics.py | >70% | 存储统计、用户关系、配额热力图 |

**lifecycle_engine 关键测试用例**:
```python
# 基础约束测试
test_delete_pool_with_teams_fails()
test_delete_pool_without_teams_succeeds()
test_upload_file_without_membership_fails()
test_upload_file_with_membership_succeeds()
test_quota_exceeded_blocks_upload()

# 边缘 case 测试
test_pool_teams_migrating_edge_case()      # POOL_TEAMS_MIGRATING
test_quota_reserved_concurrent_upload()   # QUOTA_RESERVED (已实现 FileUpload 模型)
test_member_recently_removed()            # MEMBER_RECENTLY_REMOVED
test_space_pending_requests()             # SPACE_HAS_PENDING_REQUESTS

# 配额超卖防护测试 (T9)
test_concurrent_upload_quota_lock()        # SELECT FOR UPDATE 锁定
test_quota_oversell_prevention()           # 10并发不超卖
test_lock_timeout_rollback()              # 锁等待超时回滚

# 并发邀请防护测试 (T10)
test_duplicate_invitation_unique_index()   # 数据库唯一索引
test_concurrent_invitation_atomicity()    # 事务原子性
```

**FileUpload 模型测试** (新增):
```python
# test_file_upload_service.py
test_create_upload_records_pending()       # 上传开始时创建记录
test_mark_completed_updates_status()      # 上传完成时更新状态
test_mark_failed_records_error()          # 上传失败时记录错误
test_get_quota_reserved_sums_uploads()     # 配额预留正确求和
test_cleanup_stale_uploads()              # 清理超时记录
```

#### 前端单元测试

| 模块 | 测试文件 | 工具 | 关键测试用例 |
|------|---------|------|------------|
| LifecycleInterceptor | lifecycle-interceptor.spec.js | Jest | beforeAction, 引导弹窗显示 |
| guidanceStore | guidanceStore.spec.js | Jest | 持久化、忽略状态 |
| useWebSocket | useWebSocket.spec.js | Jest | 连接、重连、消息处理 |

### 3.3 集成测试计划

#### API 端点集成测试

```python
# tests/integration/test_lifecycle_api.py

class TestLifecycleAPI:
    """生命周期 API 集成测试"""

    def test_delete_pool_constraint_api(self, client, auth_headers):
        """DELETE /api/v1/pools/{id} 约束检查"""
        # 1. 创建有团队的存储池
        # 2. 尝试删除
        # 3. 验证返回 409 + guidance
        pass

    def test_upload_file_constraint_api(self, client, auth_headers):
        """POST /api/v1/files 约束检查"""
        # 1. 非成员尝试上传
        # 2. 验证返回 403 + guidance
        pass

    def test_quota_exceeded_api(self, client, auth_headers):
        """配额超限约束检查"""
        # 1. 上传文件使配额用尽
        # 2. 尝试再次上传
        # 3. 验证返回 403 + guidance
        pass
```

#### WebSocket 集成测试

```python
# tests/integration/test_websocket.py

class TestWebSocket:
    """WebSocket 实时推送集成测试"""

    def test_admin_analytics_push(self, ws_client, auth_headers):
        """Admin 统计数据推送"""
        # 1. 建立 WebSocket 连接
        # 2. 触发数据更新操作
        # 3. 验证推送消息格式
        pass

    def test_reconnect_after_disconnect(self, ws_client):
        """断线重连测试"""
        # 1. 建立连接
        # 2. 模拟断线
        # 3. 验证自动重连
        pass
```

### 3.4 E2E 测试计划

#### 核心用户流程 E2E

```javascript
// e2e/guidance-flow.spec.js (Playwright)

test.describe('新手引导完整流程', () => {
    test('注册 → 加入团队 → 上传文件引导', async ({ page }) => {
        // 1. 注册新用户
        await page.goto('/register')
        await page.fill('#username', 'testuser')
        await page.fill('#email', 'test@example.com')
        await page.click('#registerBtn')

        // 2. 验证引导弹窗出现
        const guidanceModal = page.locator('.guidance-modal')
        await expect(guidanceModal).toBeVisible()

        // 3. 点击创建团队
        await page.click('text=创建我的团队')
        await expect(page.url()).toContain('/teams/create')

        // 4. 创建团队后验证
        // ...
    })
})

// e2e/lifecycle-constraint.spec.js

test.describe('生命周期约束流程', () => {
    test('非成员无法上传文件', async ({ page }) => {
        // 1. 以非成员身份访问空间
        // 2. 尝试上传文件
        // 3. 验证拦截提示出现
        const guidanceModal = page.locator('.guidance-modal')
        await expect(guidanceModal).toContainText('请先加入团队')
    })

    test('删除有团队的存储池失败', async ({ page }) => {
        // 1. Admin 登录
        // 2. 访问存储池管理
        // 3. 尝试删除有团队的存储池
        // 4. 验证 guidance 弹窗
    })

    test('并发上传配额不超卖', async ({ browser }) => {
        // 1. 创建 10 个并发上下文
        // 2. 同时触发上传请求
        // 3. 验证总使用量 = 配额总量
    })

    test('重复邀请返回友好错误', async ({ page }) => {
        // 1. 邀请同一成员两次
        // 2. 验证第二次返回友好错误
        // 3. 验证无重复数据库记录
    })
})
```

#### Admin 控制台 E2E

```javascript
// e2e/admin-dashboard.spec.js

test.describe('Admin 控制台', () => {
    test('存储池图表正确显示', async ({ page }) => {
        await page.goto('/admin/dashboard')
        await expect(page.locator('.storage-pool-chart')).toBeVisible()
        const poolCards = page.locator('.pool-card')
        expect(await poolCards.count()).toBeGreaterThan(0)
    })

    test('实时数据更新', async ({ page }) => {
        // 1. 打开 Admin 控制台
        // 2. 在另一标签页上传文件
        // 3. 验证 WebSocket 推送更新图表
    })

    test('配额超 90% 触发告警', async ({ page }) => {
        // 1. Admin 登录
        // 2. 设置配额使用率 > 90%
        // 3. 验证告警通知出现
        // 4. 验证告警面板有记录
    })

    test('审计日志可追溯删除操作', async ({ page }) => {
        // 1. 执行删除操作 (空间/团队/文件)
        // 2. 访问审计日志页面
        // 3. 验证操作记录存在
        // 4. 验证时间、操作者、结果正确
    })
})
```

### 3.5 测试执行计划

| 测试阶段 | 执行时机 | 工具 | 覆盖率目标 |
|---------|---------|------|-----------|
| 单元测试 | 每次代码提交 | pytest + Jest | >80% |
| 集成测试 | 每日 CI | pytest + requests | >60% |
| E2E 测试 | 发布前 | Playwright | 核心路径 |
| 性能测试 | 每月 | k6 / locust | P95 < 200ms |

### 3.6 CI/CD 集成

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend unit tests
        run: pytest tests/unit/ --cov=services --cov=engine

      - name: Run frontend unit tests
        run: pnpm test -- --coverage

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: pytest tests/integration/ -v

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run E2E tests
        run: pnpm exec playwright test

  tauri-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tauri tests
        run: |
          cd src-tauri
          cargo test
          cargo clippy -- -D warnings
```

---

## 四、质量保障清单

### 4.1 代码质量标准

| 指标 | 目标 | 当前状态 |
|------|------|---------|
| 测试覆盖率 | >80% | ~70% (需提升) |
| 圈复杂度 | <10 | ~8 (达标) |
| 代码重复率 | <5% | <3% (达标) |
| API 响应时间 | <200ms (P95) | ~150ms (达标) |

### 4.2 发布检查清单

- [ ] 所有单元测试通过
- [ ] 集成测试通过
- [ ] E2E 测试核心路径通过
- [ ] 测试覆盖率 > 80%
- [ ] 无高危安全漏洞
- [ ] 文档已更新
- [ ] Changelog 已记录

---

## 五、风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 引导系统影响性能 | 低 | 中 | 异步加载引导模块，事件节流 |
| 约束拦截误伤正常操作 | 中 | 高 | 充分测试，灰度发布 |
| WebSocket 长连接消耗资源 | 中 | 低 | 心跳机制，断线重连 |
| 引导重复显示骚扰用户 | 中 | 中 | localStorage 持久化忽略状态 |

---

## 六、相关文档

- [TOP_DOWN_DEVELOPMENT.md](./TOP_DOWN_DEVELOPMENT.md) - 自顶向下开发方法论
- [TASK_BREAKDOWN.md](./TASK_BREAKDOWN.md) - 任务分解
- [lifecycle_config.yaml](./lifecycle_config.yaml) - 约束规则配置
