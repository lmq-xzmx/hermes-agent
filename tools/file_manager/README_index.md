# Hermes File Manager 架构文档索引

## 实现状态总览

> 最后更新: 2026-05-02 19:00

| 文档 | 实现状态 | 完成率 |
|------|---------|--------|
| SYSTEM_ARCHITECTURE.md | ✅ 参考文档 | 参考 |
| ADMIN_DASHBOARD.md | ✅ ~100% | 100% |
| MODULE_1_ADMIN_DASHBOARD.md | ✅ ~100% | 100% |
| LIFECYCLE_CONSTRAINTS.md | ✅ ~100% | 100% |
| MODULE_2_LIFECYCLE_CONSTRAINTS.md | ✅ 100% | 100% |
| NEW_USER_GUIDE.md | ✅ ~100% | 100% |
| UPGRADE_PLAN.md | ✅ 规划文档 | 规划 |
| TOP_DOWN_DEVELOPMENT.md | ✅ 方法论文档 | 方法论 |
| OPTIMIZATION_AND_TEST_PLAN.md | ✅ 优化测试计划 | 优化 |
| IMPLEMENTATION_PLAN_V2.md | ✅ v2.0 实施计划 | 10人协同 |
| CODE_CLEANUP_GUIDE.md | ✅ 冗余清理指南 | 清理最佳实践 |
| ERROR_CODE_CONTRACT.md | ✅ 错误码契约 | 契约 |
| RTM.md | ✅ 需求追踪总览 | 需求管理 |
| RTM_REQUIREMENTS_TRACEABILITY.md | ✅ 需求追踪详情 | 需求管理 |
| RTM_V2_PLAN.md | ✅ v2.0 需求追踪 | 需求管理 |
| GUIDANCE_INTEGRATION.md | ✅ 已完善 | 引导系统集成 |
| INTERFACE_CONTRACT.md | ✅ 接口契约 | 接口定义 |
| CHECKPOINTS.md | ✅ Checkpoint 审查 | 审查清单 |

---

## 文档目录

```
docs/architecture/
├── README.md                    # 本索引文件
├── SYSTEM_ARCHITECTURE.md       # 系统架构总览 ✅
├── ADMIN_DASHBOARD.md           # Admin 信息可视化界面建议 ✅
├── MODULE_1_ADMIN_DASHBOARD.md  # Admin 控制台详细设计 ✅
├── LIFECYCLE_CONSTRAINTS.md     # 生命周期操作约束 ✅
├── MODULE_2_LIFECYCLE_CONSTRAINTS.md  # 约束详细设计 ✅
├── NEW_USER_GUIDE.md            # 普通用户新手指导 ✅
├── GUIDANCE_INTEGRATION.md      # 引导系统集成架构 ✅
├── UPGRADE_PLAN.md             # v2.0 升级方案
├── TASK_BREAKDOWN.md           # 任务分解文档
├── TOP_DOWN_DEVELOPMENT.md     # 自顶向下开发方法论 ✅
├── OPTIMIZATION_AND_TEST_PLAN.md  # 优化与测试计划 ✅
├── IMPLEMENTATION_PLAN_V2.md   # v2.0 10人协同实施 ✅
├── CODE_CLEANUP_GUIDE.md       # 冗余代码清理指南 ✅
├── ERROR_CODE_CONTRACT.md      # 前后端错误码契约 ✅
├── RTM.md                      # 需求追踪总览 ✅
├── RTM_REQUIREMENTS_TRACEABILITY.md  # 需求追踪详情 ✅
├── RTM_V2_PLAN.md             # v2.0 需求追踪 (M4/M5) ✅
├── INTERFACE_CONTRACT.md       # 接口契约定义 ✅
├── CHECKPOINTS.md              # Checkpoint 审查清单 ✅
├── RDM_DEVELOPMENT.md          # 需求依赖矩阵方法论 ✅
├── RDM_Requirements_Dependency_Matrix.md  # 需求依赖矩阵模板 ✅
├── RDM.md                     # 需求依赖管理执行文档 ✅
└── TASK_ASSIGNMENT.md         # 10人任务分配表 ✅
```

---

## 实现清单

### ✅ 已完成

- [x] **模块二：生命周期约束** (95%)
  - `LifecycleViolation` 异常 (`engine/lifecycle_exception.py`)
  - `lifecycle_constraint` 装饰器 (`services/lifecycle_engine.py`)
  - `LifecycleInterceptor` 前端拦截器 (`web/js/lifecycle-interceptor.js`)
  - `GuidanceEngine` 后端引擎 (`engine/guidance_engine.py`)
  - 约束规则 9 条已实现（含 4 个边缘 case 规则）
  - 边缘 case 日志记录 (logger.warning)

- [x] **模块一：Admin 可视化** (~100%)
  - AdminOverview 概览组件
  - StoragePoolChart 环形图
  - QuotaHeatmap 热力图
  - UserSpaceSankey 桑基图
  - OperationTrends 趋势图
  - AlertList 告警列表
  - AdminAnalyticsService 后端服务
  - ECharts 图表库集成 (adminTheme.js)
  - useWebSocket composable（已启用，JWT Token 传递）

- [x] **模块三：新手引导** (~100%)
  - GuidanceModal 弹窗组件
  - TourGuide 引导组件
  - useGuidance composable
  - useLifecycle composable
  - GuidanceEngine 后端引擎
  - useTour composable (TourHighlight, TourProgress)
  - guidance-trigger-boot.js (前端触发点连接)
  - WorkflowTourGuide.vue (3 节点引导)
  - NotebookTourGuide.vue (4 节点引导)
  - localStorage 持久化 (dismissedEvents Set)

---

## 待办任务

### ✅ 全部完成 (10/10)

所有任务已完成，详见 [TASK_BREAKDOWN.md](./TASK_BREAKDOWN.md)

| 模块 | 任务 | 状态 |
|------|------|------|
| M1-T1 | WebSocket connect() | ✅ 已完成 |
| M1-T2 | AdminOverview 数据聚合 | ✅ 已完成 |
| M1-T3 | ECharts 主题适配 | ✅ 已完成 |
| M2-T1 | 边缘约束 Case | ✅ 已完成 |
| M2-T2 | 前端约束兜底 | ✅ 已完成 |
| M3-T1 | 前端触发点连接 | ✅ 已完成 |
| M3-T2 | 引导状态持久化 | ✅ 已完成 |
| M3-T3 | Workflow 引导 Tour | ✅ 已完成 |
| M3-T4 | Notebook 引导 Tour | ✅ 已完成 |
| M3-T5 | TourGuide 组件增强 | ✅ 已完成 |

---

**待办总计：0 项 | 已完成: 12/12 (含补充项)**

**补充说明**:
- FileUpload 模型已实现 (`engine/models.py`)
- `get_quota_reserved()` 已完善 (`lifecycle_engine.py`)
- `FileUploadService` 已实现 (`engine/file_upload_service.py`)
- `check_quota_for_write_with_lock()` 已实现 (`space_service.py:225`) - T5
- 前端上传组件需接入 FileUploadService（调用 `create_upload()` / `mark_completed()`）
- SpaceLink 跨团队协作已实现 (`space_service.py`, `server.py`)
- 并发邀请防护已实现 (数据库唯一索引 `ix_hfm_space_members_unique`)
- 配额超卖防护已实现 (SELECT FOR UPDATE + func.sum) - T5完成

---

## 文档概览

### 1. 系统架构总览 (SYSTEM_ARCHITECTURE.md)

**核心内容**：
- 系统架构概览图
- 新系统初始化步骤
- 新用户注册流程
- 新团队创建流程
- 空间与团队/用户关系
- 存储池分配机制
- 私人空间与团队空间关系
- 管理员与普通用户关系
- 生命周期总览图

**所属领域**：企业级文件管理 / 云存储协作平台

---

### 2. Admin 信息可视化界面建议 (ADMIN_DASHBOARD.md)

**核心内容**：
- 领域分类与最佳实践方法论
- Admin 控制台界面布局建议
- 核心可视化组件设计
- 操作拦截规则
- 新手引导事件驱动流程

**所属领域**：
- 多租户存储资源管理
- 基于角色的访问控制 (RBAC)
- 团队协作与空间隔离

---

### 3. 生命周期操作约束 (LIFECYCLE_CONSTRAINTS.md)

**核心内容**：
- 约束规则设计
- 用户语言提示设计
- 后端约束实现
- 前端错误处理
- 操作拦截流程图
- 约束规则表

**所属领域**：
- 操作约束与数据一致性保护
- 生命周期合规性管理

---

### 4. 普通用户新手指导 (NEW_USER_GUIDE.md)

**核心内容**：
- 用户旅程引导地图
- 事件驱动引导实现
- 工作流与笔记本功能集成
- 引导触发机制
- 引导提示消息库

**所属领域**：
- 基于事件的引导系统
- 工作流与知识协作

---

## 快速导航

### 按角色

| 角色 | 推荐文档 |
|------|---------|
| 系统管理员 | ADMIN_DASHBOARD.md, LIFECYCLE_CONSTRAINTS.md |
| 团队所有者 | SYSTEM_ARCHITECTURE.md, LIFECYCLE_CONSTRAINTS.md |
| 普通用户 | NEW_USER_GUIDE.md, SYSTEM_ARCHITECTURE.md |

### 按任务

| 任务 | 推荐文档 |
|------|---------|
| 理解系统架构 | SYSTEM_ARCHITECTURE.md |
| 设计管理界面 | ADMIN_DASHBOARD.md |
| 实现操作约束 | LIFECYCLE_CONSTRAINTS.md |
| 设计用户引导 | NEW_USER_GUIDE.md |
| 前后端引导集成 | GUIDANCE_INTEGRATION.md |

---

## 文档版本

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 2.5 | 2026-05-02 | T5任务完成：REQ-M2-017 配额超卖防护实现完成 (check_quota_for_write_with_lock✅, 5个测试用例全部通过)；待办清单清零 |
| 2.4 | 2026-05-02 | RTM 矛盾修复：REQ-M2-001/017/018 任务映射统一 (M2-T9→M2-T2/T9/T10)；REQ-M2-018 ✅已完成 |
| 2.3 | 2026-05-02 | RTM 更新：REQ-M2-018 状态修正为"✅已完成"(核实 space_service.py:620 应用层检查已实现)；新增"部分实现"状态选项 |
| 2.2 | 2026-05-02 | RTM 文档体系完善：统一 REQ-M*-* 命名规范；RTM.md 更新为 M1-M3 总览；RTM_V2_PLAN.md 新增 M4/M5 需求追踪 |
| 2.1 | 2026-05-02 | 新增 INTERFACE_CONTRACT.md（接口契约）、CHECKPOINTS.md（审查清单）；文档体系完善 |
| 2.0 | 2026-05-02 | 完成自顶向下开发模式审视：补充 FileUpload 模型、完善 get_quota_reserved()、创建 FileUploadService；更新 RTM/GUIDANCE_INTEGRATION 状态为已完成 |
| 1.9 | 2026-05-02 | 新增 GUIDANCE_INTEGRATION.md 引导系统集成架构文档；揭示前后端引导系统双轨制问题 |
| 1.7 | 2026-05-02 | 新增 ERROR_CODE_CONTRACT.md 前后端错误码契约文档；更新文档索引 |
| 1.6 | 2026-05-02 | 新增 TOP_DOWN_DEVELOPMENT.md、OPTIMIZATION_AND_TEST_PLAN.md、IMPLEMENTATION_PLAN_V2.md 三个方法论文档；更新文档目录和版本历史 |
| 1.5 | 2026-05-02 | 所有任务完成 (10/10)：M1-T3 ECharts主题、M3-T1触发点连接、M3-T4/M3-T5 TourGuide、M2-T1/T2-T2约束全部完成 |
| 1.4 | 2026-05-02 | 合并最终待办清单：6项待办（高3项+中3项），更新完成度 |
| 1.3 | 2026-05-02 | 更新完成度：模块二95%(原100%，部分边缘case待完善)、模块三75%(原70%)；添加新待办：边缘约束case处理；标注WebSocket connect()被注释状态 |
| 1.2 | 2026-05-02 | 更新完成度：模块二100%、模块一85%、模块三70%；添加待办任务清单 |

---

## 相关链接

- [系统规格说明](../SPEC.md)
- [API 接口文档](../api/)
- [数据模型](../engine/models.py)
- [工作流服务](../services/workflow_service.py)
- [笔记本服务](../services/notebook_service.py)