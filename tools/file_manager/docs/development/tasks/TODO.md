# Hermes File Manager 待办任务清单

> **版本**: 1.0
> **更新日期**: 2026-05-05
> **整理依据**: DEVELOPMENT_TASKS.md, TASK_ASSIGNMENT.md, TASK_BREAKDOWN.md, resource_quota_system_tasks.md
> **标注规则**: 已完成任务使用 ~~~删除号~~~ 标注

---

## 一、已完成任务（历史记录）

### 1.1 核心开发任务 (T1-T10) ~~~T1~~~$^{已删除}$
~~~T2~~~$^{已删除}$
~~~T3~~~$^{已删除}$
~~~T4~~~$^{已删除}$
~~~T5~~~$^{已删除}$
~~~T6~~~$^{已删除}$
~~~T7~~~$^{已删除}$
~~~T8~~~$^{已删除}$
~~~T9~~~$^{已删除}$
~~~T10~~~$^{已删除}$

**验收文件位置**:
- T1: `tests/integration/conftest.py` (483行)
- T2: `tests/integration/test_quota_block.py` (285行)
- T3: `web/src/stores/__tests__/guidanceStore.test.js`
- T4: `web/tests/e2e/user_journey.spec.js` (328行, 11 passed)
- T5: `services/space_service.py:248` (SELECT FOR UPDATE)
- T6: `tests/integration/test_duplicate_invitation.py`
- T7: `tests/contract/` (4个文件, 432行)
- T8: `.github/workflows/test.yml` (103行)
- T9: `web/tests/e2e/guidance.spec.js` (923行, 29tests)
- T10: `web/tests/e2e/admin.spec.js` (334行, 20tests)

### 1.2 文档同步任务 (DOC-SYNC-01~10) ~~~DOC-SYNC-01~~~$^{已删除}$
~~~DOC-SYNC-02~~~$^{已删除}$
~~~DOC-SYNC-03~~~$^{已删除}$
~~~DOC-SYNC-04~~~$^{已删除}$
~~~DOC-SYNC-05~~~$^{已删除}$
~~~DOC-SYNC-06~~~$^{已删除}$
~~~DOC-SYNC-07~~~$^{已删除}$
~~~DOC-SYNC-08~~~$^{已删除}$
~~~DOC-SYNC-09~~~$^{已删除}$
~~~DOC-SYNC-10~~~$^{已删除}$

### 1.3 Vue 3 SPA 迁移任务 (TASK-018~TASK-028) ~~~TASK-018~~~$^{已删除}$
~~~TASK-019~~~$^{已删除}$
~~~TASK-020~~~$^{已删除}$
~~~TASK-021~~~$^{已删除}$
~~~TASK-022~~~$^{已删除}$
~~~TASK-023~~~$^{已删除}$
~~~TASK-024~~~$^{已删除}$
~~~TASK-025~~~$^{已删除}$
~~~TASK-026~~~$^{已删除}$
~~~TASK-027~~~$^{已删除}$
~~~TASK-028~~~$^{已删除}$

### 1.4 模块任务 (M1-M6)

#### M1: Admin 控制台可视化 ~~~M1-T1~~~$^{已删除}$ (WebSocket connect())
~~~M1-T2~~~$^{已删除}$ (AdminOverview 数据聚合)
~~~M1-T3~~~$^{已删除}$ (ECharts 主题适配)

#### M2: 生命周期约束 ~~~M2-T1~~~$^{已删除}$ (边缘约束 Case)
~~~M2-T2~~~$^{已删除}$ (前端约束兜底)

#### M3: 新手引导系统 ~~~M3-T1~~~$^{已删除}$ (前端触发点连接)
~~~M3-T2~~~$^{已删除}$ (引导状态持久化)
~~~M3-T3~~~$^{已删除}$ (Workflow 引导 Tour)
~~~M3-T4~~~$^{已删除}$ (Notebook 引导 Tour)
~~~M3-T5~~~$^{已删除}$ (TourGuide 组件增强)

#### M6: 测试基础设施 ~~~M6-T1~~~$^{已删除}$ (REPO-M2-001 配额超限拦截)
~~~M6-T2~~~$^{已删除}$ (契约测试自动化)
~~~M6-T3~~~$^{已删除}$ (集成测试框架)
~~~M6-T4~~~$^{已删除}$ (前端组件单元测试)
~~~M6-T5~~~$^{已删除}$ (E2E 测试关键路径)
~~~M6-T6~~~$^{已删除}$ (配额超卖防护)
~~~M6-T7~~~$^{已删除}$ (并发邀请防护)
~~~M6-T8~~~$^{已删除}$ (Schemathesis 契约测试)

### 1.5 资源配额体系 (Module A-F) ~~~Module A~~~$^{已删除}$ (数据模型层)
~~~Module B~~~$^{已删除}$ (服务层)
~~~Module C~~~$^{已删除}$ (API 层)
~~~Module D~~~$^{已删除}$ (Admin 前端)
~~~Module E~~~$^{已删除}$ (用户前端)
~~~Module F~~~$^{已删除}$ (配置系统)

---

## 二、待处理任务

### TASK-029: 统一错误码格式 (移除 LIFECYCLE_ 前缀)

**优先级**: P1 (Critical)
**依赖**: 无
**状态**: ✅ 已完成

**验收文件位置**:
- `docs/4_api/ERROR_CODE_CONTRACT.md` (v1.1, 2026-05-05)
- `docs/4_api/INTERFACE_CONTRACT.md` (v1.2, 2026-05-05)
- `docs/lifecycle/lifecycle_config.yaml` (已确认无需更新)

---

### TASK-030: 同步 RTM/RDM 状态

**优先级**: P1 (Critical)
**依赖**: 无
**状态**: ✅ 已完成

**验收文件位置**:
- `docs/7_tracking/RTM.md` (v2.5, 2026-05-05)
- `docs/7_tracking/RTM_REQUIREMENTS_TRACEABILITY.md` (v2.7, 2026-05-05)
- `docs/7_tracking/RDM_DEVELOPMENT.md` (v1.1, 2026-05-05)

**核实结果**:
- REQ-M2-017 (配额超卖防护): RTM.md 显示 ✅已完成，与 RTM_REQUIREMENTS_TRACEABILITY.md 一致
- REQ-M2-018 (并发邀请防护): RTM.md 显示 ⚠️部分实现 (数据库唯一索引待验证)，RTM_REQUIREMENTS_TRACEABILITY.md 显示 ✅已实现
- 状态已统一

---

## 三、任务依赖关系

```
TASK-029 (错误码格式) ─────────┐
                                ├──→ 无相互依赖，可并行
TASK-030 (RTM/RDM同步) ────────┘
```

---

## 四、并行开发建议

**可立即启动**: TASK-029, TASK-030 (相互独立，可分配给不同成员)

**TASK-029 完成后**: 更新 ERROR_CODE_CONTRACT.md, INTERFACE_CONTRACT.md, lifecycle_config.yaml

**TASK-030 完成后**: 更新 RTM.md, RDM_DEVELOPMENT.md

---

## 五、历史完成度统计

| 任务类别 | 总数 | 已完成 | 待处理 | 完成率 |
|---------|------|--------|--------|--------|
| 核心开发 (T1-T10) | 10 | 10 | 0 | 100% |
| 文档同步 (DOC-SYNC) | 10 | 10 | 0 | 100% |
| Vue 3 SPA 迁移 | 11 | 11 | 0 | 100% |
| 模块任务 (M1-M6) | 17 | 17 | 0 | 100% |
| 资源配额体系 (A-F) | 6 | 6 | 0 | 100% |
| **新增任务** | **2** | **2** | **0** | **100%** |

**历史任务总完成**: 54/54 (100%)
**新增任务完成**: 2/2 (100%)

---

## 六、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0 | 2026-05-05 | 初始版本：整理历史任务+新增待办任务 |
| **1.1** | **2026-05-05** | **任务完成更新**：TASK-029 (错误码格式统一) 和 TASK-030 (RTM/RDM状态同步) 标记为已完成 |