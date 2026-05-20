# 需求追踪矩阵 (Requirements Traceability Matrix)

> **版本**: 2.7
> **更新日期**: 2026-05-05
> **目的**: 建立需求→任务→代码→测试的完整追踪链路
> **命名规范**: 统一采用 `REQ-{模块}-{序号}` 格式
> **同步状态**: 与 RTM.md 保持一致；M4/M5 需求已移至 RTM_V2_PLAN.md
> **更新说明 v2.6**: REQ-M6-002/003/005/006 全部验证通过；T2 test_quota_block.py (6用例) 修复后全部通过
> **更新说明 v2.5**: REQ-M6-002 新增 test_lifecycle_api.py (19个测试用例全部通过)
> **更新说明 v2.3**: T5任务完成，REQ-M2-017状态更新为✅已实现 (5个测试用例全部通过)
> **更新说明 v2.2**: CONF-003 用户选择A，REQ-M3-001改为"前端引导触发点框架"
> **更新说明 v2.1**: 修正 REQ-M2-001/017/018 任务映射 (M2-T9→M2-T2/T9/T10)；统一任务编号来源
> **更新说明 v2.0**: 统一命名规范 REQ-M*-*，修正 REQ-M2-001 状态，M4/M5 移至独立文档

---

## 一、RTM 概述

### 1.1 什么是 RTM

RTM (Requirements Traceability Matrix) 是一种需求管理工具，用于确保：
- 每个需求都有对应的实现
- 每个实现都有对应的测试
- 每个测试都能验证需求

### 1.2 为什么需要 RTM

| 问题 | 无 RTM | 有 RTM |
|------|--------|--------|
| 需求遗漏 | ❌ 开发后发现 | ✅ 早期识别 |
| 需求变更影响 | ❌ 难以评估 | ✅ 快速定位 |
| 测试覆盖 | ❌ 可能有盲区 | ✅ 全部覆盖 |
| 交付物验收 | ❌ 不确定是否完成 | ✅ 有据可查 |

---

## 二、RTM 结构

### 2.1 核心字段

| 字段 | 说明 | 示例 |
|------|------|------|
| REQ-ID | 需求唯一标识 | REQ-M2-001 |
| 描述 | 需求简要描述 | 配额超限时拦截上传 |
| 优先级 | P0/P1/P2/P3 | P0 |
| 模块 | 所属大模块 | M2 (生命周期约束) |
| 任务 | 对应子任务 | T9 (配额超卖防护) |
| 代码位置 | 实现文件 | services/lifecycle_engine.py |
| 测试用例 | 对应测试 | test_quota_exceeded_blocks_upload |
| 状态 | 已实现/待开发/变更中 | ✅ 已实现 |

### 2.2 RTM 矩阵模板

```
| REQ-ID      | 描述              | 优先级 | 模块 | 任务        | 代码位置                    | 测试用例                        | 状态 |
|-------------|-------------------|--------|------|-------------|-----------------------------|--------------------------------|------|
| REQ-M2-001  | 配额超限拦截       | P0     | M2   | M2-T2      | lifecycle_engine.py:270      | test_quota_exceeded_blocks_... | ✅   |
| REQ-M2-002  | 非成员禁止上传     | P0     | M2   | M2-T2      | lifecycle_engine.py:272     | test_upload_file_without_...   | ✅   |
| ...         | ...               | ...    | ...  | ...         | ...                         | ...                            | ...  |
```

---

## 三、v2.0 需求追踪矩阵

### 3.1 模块一：Admin 可视化 (M1)

| REQ-ID | 描述 | 优先级 | 任务 | 代码位置 | 测试用例 | 状态 |
|--------|------|--------|------|----------|----------|------|
| REQ-M1-001 | WebSocket 实时数据推送 | P0 | M1-T1 | useWebSocket.js | test_ws_realtime_push | ✅ |
| REQ-M1-002 | AdminOverview 数据聚合 | P0 | M1-T2 | AdminOverview.vue | test_admin_overview | ✅ |
| REQ-M1-003 | ECharts 暗色主题适配 | P1 | M1-T3 | adminTheme.js | N/A (可视化) | ✅ |
| REQ-M1-004 | 存储池环形图 | P1 | M1-T2 | StoragePoolChart.vue | test_storage_pool_chart | ✅ |
| REQ-M1-005 | 操作趋势折线图 | P2 | M1-T2 | OperationTrends.vue | N/A (可视化) | ✅ |
| REQ-M1-006 | 用户-空间桑基图 | P2 | M1-T2 | UserSpaceSankey.vue | N/A (可视化) | ✅ |
| REQ-M1-007 | 配额热力图 | P2 | M1-T2 | QuotaHeatmap.vue | N/A (可视化) | ✅ |
| REQ-M1-008 | 告警列表组件 | P1 | M1-T2 | AlertList.vue | test_alert_list | ✅ |

### 3.2 模块二：生命周期约束 (M2)

> **状态说明**:
> - ✅ 已实现: 全部完成
> - ⚠️ 部分实现: 部分完成，需补充
> - ❌ 未实现: 待开发
> - 🔄 变更中: 实施中

| REQ-ID | 描述 | 优先级 | 任务 | 代码位置 | 测试用例 | 状态 |
|--------|------|--------|------|----------|----------|------|
| REQ-M2-001 | 配额超限拦截 | P0 | M2-T2 | lifecycle_engine.py:157 | test_quota_exceeded_blocks_upload | ✅ 已实现 |
| REQ-M2-002 | 非成员禁止上传 | P0 | M2-T2 | lifecycle_engine.py:272 | test_upload_file_without_membership | ✅ |
| REQ-M2-003 | 无可用存储池禁止创建团队 | P0 | M2-T2 | lifecycle_engine.py:244 | test_create_team_without_pool | ✅ |
| REQ-M2-004 | 非团队成员禁止创建私人空间 | P0 | M2-T2 | lifecycle_engine.py:260 | test_create_private_space_not_member | ✅ |
| REQ-M2-005 | 存储池有团队时禁止删除 | P0 | M2-T1 | lifecycle_engine.py:195 | test_delete_pool_with_teams | ✅ |
| REQ-M2-006 | 空间有成员时禁止删除 | P0 | M2-T1 | lifecycle_engine.py:215 | test_delete_space_with_members | ✅ |
| REQ-M2-007 | 非所有者禁止邀请成员 | P0 | M2-T2 | lifecycle_engine.py:226 | test_invite_member_not_owner | ✅ |
| REQ-M2-008 | 非所有者禁止删除团队 | P0 | M2-T1 | lifecycle_engine.py:305 | test_delete_team_not_owner | ✅ |
| REQ-M2-009 | 非所有者禁止修改配额 | P1 | M2-T2 | lifecycle_engine.py:326 | test_update_quota_not_owner | ✅ |
| REQ-M2-010 | 凭证无效时禁止加入团队 | P1 | M2-T1 | lifecycle_engine.py:342 | test_join_team_invalid_credential | ✅ |
| REQ-M2-011 | POOL_MIGRATING 边缘 case | P1 | M2-T1 | lifecycle_engine.py:64 | test_pool_teams_migrating | ✅ |
| REQ-M2-012 | QUOTA_RESERVED 并发边缘 case | P1 | M2-T1 | lifecycle_engine.py:84 | test_quota_reserved_concurrent | ✅ 已实现 (FileUpload 模型) |
| REQ-M2-013 | MEMBER_RECENTLY_REMOVED 边缘 case | P1 | M2-T1 | lifecycle_engine.py:141 | test_member_recently_removed | ✅ |
| REQ-M2-014 | SPACE_HAS_PENDING_REQUESTS 边缘 case | P1 | M2-T1 | lifecycle_engine.py:232 | test_space_pending_requests | ✅ |
| REQ-M2-015 | 前端约束兜底 | P1 | M2-T2 | web/src/components/lifecycle/LifecycleInterceptor.vue | test_lifecycle_interceptor | ✅ 已实现 |
| REQ-M2-016 | 边缘约束 Case 完善 | P1 | M2-T1 | lifecycle_engine.py (4个边缘case方法) | test_pool_teams_migrating, test_member_recently_removed 等 | ✅ 已实现 |
| REQ-M2-017 | 配额超卖防护 (SELECT FOR UPDATE) | P0 | T5 | space_service.py:225 (check_quota_for_write_with_lock) + FileUpload模型 | test_concurrent_upload_quota_lock (5用例) | ✅ 已实现 |
| REQ-M2-018 | 并发邀请防护 (唯一索引) | P0 | T10 | models.py: ix_hfm_space_members_unique + space_service.py:620,719,884 | test_duplicate_invitation_unique_index (4用例) | ✅ 已实现 |
| REQ-M2-019 | 跨团队协作 (SpaceLink) | P1 | T11 | space_service.py, server.py | test_space_link_cross_team | ✅ 已实现 |

### 3.3 模块三：新手引导 (M3)

| REQ-ID | 描述 | 优先级 | 任务 | 代码位置 | 测试用例 | 状态 |
|--------|------|--------|------|----------|----------|------|
| REQ-M3-001 | 前端引导触发点框架 (支持10+触发场景) | P1 | M3-T1 | guidance-trigger-boot.js | test_trigger_framework | ✅ 已实现，待E2E验证 |
| REQ-M3-002 | 加入团队后触发引导 | P1 | M3-T1 | guidance-trigger-boot.js | test_team_joined_trigger | ✅ |
| REQ-M3-003 | 上传文件后触发引导 | P1 | M3-T1 | guidance-trigger-boot.js | test_file_uploaded_trigger | ✅ |
| REQ-M3-004 | 引导状态 localStorage 持久化 | P1 | M3-T2 | guidanceStore.js | test_guidance_persistence | ✅ |
| REQ-M3-005 | Workflow 创建步骤引导 | P1 | M3-T3 | WorkflowTourGuide.vue | test_workflow_tour_navigation | ✅ |
| REQ-M3-006 | Notebook 创建步骤引导 | P1 | M3-T4 | NotebookTourGuide.vue | test_notebook_tour_navigation | ✅ |
| REQ-M3-007 | 引导弹窗组件 (GuidanceModal) | P0 | M3-T4 | GuidanceModal.vue | test_guidance_modal_display | ✅ |
| REQ-M3-008 | TourHighlight 高亮遮罩 | P1 | M3-T5 | useTour.js | test_tour_highlight | ✅ |
| REQ-M3-009 | TourProgress 步骤指示器 | P2 | M3-T5 | useTour.js | test_tour_progress | ✅ |
| REQ-M3-010 | 配额警告触发引导 | P2 | M3-T1 | guidance-trigger-boot.js | test_quota_warning_trigger | ✅ |
| REQ-M3-011 | 跨团队协作触发引导 | P3 | M3-T1 | guidance-trigger-boot.js | test_cross_team_collab_trigger | ✅ |

### 3.4 测试与基础设施需求 (M6)

> **模块状态**: ✅ 部分实现 (T2/T5/T6集成测试已完成通过，T3前端测试已完成)
> **更新说明 v2.7**: 前端测试扩展至60个用例全部通过；新增fileUtils.test.js(19用例)、api.contract.test.js(12用例)
> **更新说明 v2.6**: REQ-M6-002/003/005/006 全部验证通过；T2 test_quota_block.py (6用例) 修复后全部通过

| REQ-ID | 描述 | 优先级 | 任务 | 代码位置 | 测试用例 | 状态 |
|--------|------|--------|------|----------|----------|------|
| REQ-M6-001 | 前后端契约测试自动化 | P1 | M6-T2 | tests/contract/ | api.test.js (12用例) | ✅ 已实现 (12/12通过) |
| REQ-M6-002 | 集成测试框架搭建 | P0 | M6-T2 | tests/integration/ | test_lifecycle_api.py (19用例) + test_quota_block.py (6用例) | ✅ 已实现 (25/25通过) |
| REQ-M6-003 | 前端组件单元测试 | P1 | M6-T1 | web/src/components/__tests__/ + stores + utils + contract | AdminOverview.test.js (16) + guidanceStore.test.js (13) + fileUtils.test.js (19) + api.test.js (12) | ✅ 已实现 (60/60通过) |
| REQ-M6-004 | E2E 测试关键路径覆盖 | P1 | M6-T3 | web/tests/e2e/ | user_journey.spec.js + guidance.spec.js + admin.spec.js | ⚠️ 前端未完成 (路由未配置，/admin返回登录页) |
| REQ-M6-005 | 配额超卖防护集成测试 | P0 | T9 | tests/integration/ | test_concurrent_upload_quota.py (5用例) | ✅ 已实现 (5/5通过) |
| REQ-M6-006 | 并发邀请防护集成测试 | P0 | T10 | tests/test_lifecycle_integration.py | TestDuplicateInvitationPrevention (4用例) | ✅ 已实现 (4/4通过) |

### 3.5 空间管理与团队配额 (M7)

> **模块状态**: ✅ 已实现

| REQ-ID | 描述 | 优先级 | 任务 | 代码位置 | 测试用例 | 状态 |
|--------|------|--------|------|----------|----------|------|
| REQ-M7-001 | 双层权限模型 | P1 | M7-T1 | models.py (Space/Team) | test_space_team_permission | ✅ 已实现 |
| REQ-M7-002 | 配额分配公式 | P1 | M7-T1 | quota_service.py | test_quota_allocation_formula | ✅ 已实现 |
| REQ-M7-003 | 成员加入自动配额划拨 | P0 | M7-T2 | space_service.py:join_team | test_auto_quota_allocation | ✅ 已实现 |
| REQ-M7-004 | 成员主动退出需审批 | P1 | M7-T2 | space_service.py:leave_team | test_leave_team_approval | ✅ 已实现 |
| REQ-M7-005 | 管理员移除成员通知 | P2 | M7-T3 | notification_service.py | test_remove_member_notification | ✅ 已实现 |
| REQ-M7-006 | 回收操作 | P1 | M7-T3 | space_service.py:recycle_space | test_space_recycle_operation | ✅ 已实现 |
| REQ-M7-007 | 待办任务入口 | P2 | M7-T3 | web/src/components/TodoEntry.vue | test_todo_entry_ui | ✅ 已实现 |
| REQ-M7-008 | 通知机制 | P1 | M7-T3 | notification_service.py | test_notification_mechanism | ✅ 已实现 |

---

## 四、测试覆盖追踪

### 4.1 测试覆盖率矩阵

| REQ-ID | 单元测试 | 集成测试 | E2E 测试 | 覆盖率 |
|--------|----------|----------|----------|--------|
| REQ-M1-001 | ✅ | ✅ | ❌ | 66% |
| REQ-M1-002 | ✅ | ✅ | ❌ | 66% |
| REQ-M2-001 | ✅ | ❌ | ❌ | 50% |
| REQ-M2-002 | ✅ | ✅ | ✅ | 100% |
| REQ-M2-017 | ❌ | ❌ | ❌ | 0% |
| REQ-M3-001 | ✅ | ❌ | ❌ | 50% |
| REQ-M3-005 | ✅ | ❌ | ❌ | 50% |

### 4.2 覆盖率目标

| 指标 | 当前值 | 目标值 | 差距 |
|------|--------|--------|------|
| 单元测试覆盖率 | ~70% | >85% | -15% |
| 集成测试覆盖率 | ~40% | >60% | -20% |
| E2E 测试覆盖率 | ~20% | >50% | -30% |
| 需求覆盖率 | 80% | 100% | -20% |

---

## 五、需求变更追踪

### 5.1 变更申请流程

```
┌─────────────┐
│  需求变更   │ ──> 填写变更申请表
└─────────────┘
       ↓
┌─────────────┐
│ 影响分析    │ ──> 评估对代码/测试/文档的影响
└─────────────┘
       ↓
┌─────────────┐
│  RTM 更新   │ ──> 更新矩阵中的状态
└─────────────┘
       ↓
┌─────────────┐
│  实施验证   │ ──> 确认变更已实现
└─────────────┘
```

### 5.2 变更记录表

| 变更日期 | REQ-ID | 变更内容 | 原因 | 审批人 | 影响范围 |
|----------|--------|----------|------|--------|----------|
| 2026-05-02 | REQ-M2-012 | 新增 QUOTA_RESERVED 边缘 case | 自顶向下审视补充 | - | lifecycle_engine.py |
| 2026-05-02 | REQ-M2-017 | 新增 M2-T9 配额超卖防护 | OPTIMIZATION_AND_TEST_PLAN | - | 待开发 |
| 2026-05-02 | REQ-M2-017 | 配额超卖防护实现完成 (SELECT FOR UPDATE + func.sum) | T5任务执行 | - | space_service.py:225, test_concurrent_upload_quota.py (5/5 passed) |
| 2026-05-02 | REQ-M2-018 | 新增 M2-T10 并发邀请防护 | OPTIMIZATION_AND_TEST_PLAN | - | 待开发 |

---

## 六、RTM 维护流程

### 6.1 维护责任人

| 角色 | 职责 |
|------|------|
| 产品经理 | 需求录入、变更审批 |
| 技术负责人 | 代码位置确认、任务分配 |
| 测试负责人 | 测试用例维护、覆盖率统计 |

### 6.2 更新时机

| 时机 | 更新内容 |
|------|----------|
| Sprint 开始 | 确认需求状态 |
| Sprint 结束 | 更新实施状态 |
| 需求变更 | 更新影响范围 |
| 测试完成 | 更新测试覆盖率 |

### 6.3 检查清单

```
RTM 维护检查清单：

- [ ] 新增需求已录入 RTM
- [ ] 需求有对应的任务分解
- [ ] 每个任务有代码位置记录
- [ ] 每个需求有测试用例覆盖
- [ ] 状态已更新为最新
- [ ] 变更已记录
```

---

## 七、相关文档

- [TOP_DOWN_DEVELOPMENT.md](./TOP_DOWN_DEVELOPMENT.md) - 自顶向下开发方法论
- [OPTIMIZATION_AND_TEST_PLAN.md](./OPTIMIZATION_AND_TEST_PLAN.md) - 优化与测试计划
- [IMPLEMENTATION_PLAN_V2.md](./IMPLEMENTATION_PLAN_V2.md) - v2.0 实施计划
- [ERROR_CODE_CONTRACT.md](./ERROR_CODE_CONTRACT.md) - 前后端错误码契约
- [TASK_BREAKDOWN.md](./TASK_BREAKDOWN.md) - 任务分解参考
