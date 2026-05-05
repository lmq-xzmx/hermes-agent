# Hermes File Manager 文档索引

> **更新日期**: 2026-05-05
> **架构**: Web优先 + Tauri壳模式 (Vue 3 SPA)

---

## 目录结构

```
docs/
├── 1_architecture/      # 架构文档
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── CROSS_PLATFORM_UI_DESIGN.md
│   └── TOP_DOWN_DEVELOPMENT.md
├── 2_design/             # 设计文档
│   ├── domain_table.md
│   ├── best_practices.md
│   ├── LIFECYCLE_CONSTRAINTS.md
│   ├── MODULE_1_ADMIN_DASHBOARD.md
│   └── MODULE_2_LIFECYCLE_CONSTRAINTS.md
├── 3_implementation/      # 实现文档
│   ├── ADMIN_DASHBOARD.md
│   ├── NEW_USER_GUIDE.md
│   ├── quota_management.md
│   ├── role_permission_design.md
│   └── resource_approval_flow.md
├── 4_api/                # API 契约文档
│   ├── ERROR_CODE_CONTRACT.md
│   ├── INTERFACE_CONTRACT.md
│   └── lifecycle_config.yaml (仅供参考)
├── 5_verification/       # 验证文档
│   ├── CHECKPOINTS.md
│   ├── GUIDANCE_INTEGRATION.md
│   └── TEST_PLAN.md
├── 6_process/            # 流程文档
│   ├── CODE_CLEANUP_GUIDE.md
│   ├── IMPLEMENTATION_PLAN_V2.md
│   ├── OPTIMIZATION_AND_TEST_PLAN.md
│   └── UPGRADE_PLAN.md
├── 7_tracking/           # 追踪文档
│   ├── RDM_DEVELOPMENT.md
│   ├── RDM_Requirements_Dependency_Matrix.md
│   ├── RDM.md
│   ├── RTM_DEVELOPMENT.md
│   ├── RTM_REQUIREMENTS_TRACEABILITY.md
│   ├── RTM_V2_PLAN.md
│   └── RTM.md
├── adr/                  # 架构决策记录
│   ├── ADR-001-web-first-architecture.md
│   ├── ADR-002-ssot-build-strategy.md
│   ├── ADR-003-tauri-shell-minimal-maintenance.md
│   ├── ADR-004-llm-wiki-migration.md
│   ├── ADR-005-api-base-unification.md
│   ├── ADR-006-build-failure-rollback.md
│   ├── ADR-007-up-url-workaround.md
│   └── README.md
├── "Web优先 + Tauri壳"模式/  # 架构模式文档
│   ├── GOALS.md
│   ├── RTM.md
│   └── RDM_Requirements_Dependency_Matrix.md
├── web/vue改造/          # Vue 3 迁移文档
│   ├── FEATURES.md
│   └── VUE3迁移工作文档.md
└── development/tasks/    # 任务管理
    ├── DEVELOPMENT_TASKS.md
    ├── TASK_ASSIGNMENT.md
    ├── TASK_BREAKDOWN.md
    └── resource_quota_system_tasks.md
```

---

## 分类文档

### 3_implementation - 实现设计文档

| 文档 | 说明 |
|------|------|
| ADMIN_DASHBOARD.md | Admin信息可视化界面建议 |
| NEW_USER_GUIDE.md | 普通用户新手指导 |
| quota_management.md | 配额管理体系设计 |
| role_permission_design.md | 角色权限设计方案 |
| resource_approval_flow.md | 资源申请审批流程 |

### lifecycle - 系统架构与生命周期约束

| 文档 | 说明 |
|------|------|
| SYSTEM_ARCHITECTURE.md | 系统架构总览 |
| ADMIN_DASHBOARD.md | Admin信息可视化界面建议 |
| MODULE_1_ADMIN_DASHBOARD.md | Admin控制台详细设计 |
| LIFECYCLE_CONSTRAINTS.md | 生命周期操作约束 |
| MODULE_2_LIFECYCLE_CONSTRAINTS.md | 约束详细设计 |
| NEW_USER_GUIDE.md | 普通用户新手指导 |
| CHECKPOINTS.md | Checkpoint审查清单 |
| TOP_DOWN_DEVELOPMENT.md | 自顶向下开发方法论 |
| lifecycle_config.yaml | 生命周期配置文件 |
| role_permission_design.md | 角色权限设计方案 |
| resource_approval_flow.md | 资源申请审批流程 |
| quota_management.md | 配额管理体系设计 |
| domain_table.md | 领域分析总表 |
| best_practices.md | 最佳实践领域管理表 |
| **CROSS_PLATFORM_UI_DESIGN.md** | **跨平台 UI/UE 设计规范 (Finder/Windows 风格)** |

### plan - 实施与优化计划

| 文档 | 说明 |
|------|------|
| IMPLEMENTATION_PLAN_V2.md | v2.0实施计划 |
| OPTIMIZATION_AND_TEST_PLAN.md | 优化与测试计划 |
| UPGRADE_PLAN.md | v2.0升级方案 |
| CODE_CLEANUP_GUIDE.md | 冗余代码清理指南 |
| ERROR_CODE_CONTRACT.md | 前后端错误码契约 |
| INTERFACE_CONTRACT.md | 接口契约定义 |

### rtm - 需求追踪矩阵

| 文档 | 说明 |
|------|------|
| RTM.md | 需求追踪总览 |
| RTM_DEVELOPMENT.md | RTM方法论 |
| RTM_REQUIREMENTS_TRACEABILITY.md | 需求追踪详情 |
| RTM_V2_PLAN.md | v2.0需求追踪(M4/M5) |

### rdm - 需求依赖矩阵

| 文档 | 说明 |
|------|------|
| RDM.md | 需求依赖管理执行文档 |
| RDM_DEVELOPMENT.md | RDM方法论 |
| RDM_Requirements_Dependency_Matrix.md | 需求依赖矩阵 |

### tasks - 任务管理

| 文档 | 说明 |
|------|------|
| TASK_BREAKDOWN.md | 任务分解单 |
| TASK_ASSIGNMENT.md | 10人任务分配表 |
| DEVELOPMENT_TASKS.md | 角色/审批/配额开发任务分配 |

### test - 测试相关

| 文档 | 说明 |
|------|------|
| TEST_PLAN.md | 测试计划 |
| GUIDANCE_INTEGRATION.md | 引导系统集成架构 |

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| **v2.0** | **2026-05-05** | **目录结构更新**: 对齐 Web优先+Tauri壳模式，添加 1_architecture~7_tracking/adr 目录结构 |
| v1.0 | 2026-05-02 | 初始版本 |

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| **3.3** | **2026-05-03** | **新增设计文档**：CROSS_PLATFORM_UI_DESIGN.md (Mac Finder/Windows 文件管理器 UI/UE 设计规范) |
| **3.2** | **2026-05-03** | **新增开发任务**：DEVELOPMENT_TASKS.md (角色/审批/配额 10人并行任务) |
| **3.1** | **2026-05-03** | **新增设计文档**：role_permission_design.md、resource_approval_flow.md、quota_management.md、domain_table.md、best_practices.md |
| 3.0 | 2026-05-02 | 重组文档目录：lifecycle/plan/rtm/rdm/tasks/test |
| 2.5 | 2026-05-02 | T5任务完成：配额超卖防护实现 |
| 2.0 | 2026-05-02 | 完成自顶向下开发模式审视 |