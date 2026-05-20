# Checkpoint 审查清单

> **版本**: 1.1
> **更新日期**: 2026-05-05
> **目的**: 定义关键审查节点，确保自顶向下开发的质量门禁
> **适用架构**: Vue 3 + Pinia + Tauri (Web 优先 + 桌面壳模式)

---

## 一、Checkpoint 概览

| Checkpoint | 时机 | 负责人 | 输出 |
|------------|------|--------|------|
| Architecture Review | Sprint 开始 (Day 1) | 架构师 | 架构设计评审报告 |
| Interface Review | 任务实现前 | Tech Lead | 接口契约确认 |
| Code Review | PR 时 | Reviewer | Code Review 清单 |
| Integration Check | Sprint 结束 (Day 14) | 全团队 | 集成验证报告 |

---

## 二、Architecture Review Checklist (Sprint 开始)

### 2.1 架构合理性

- [ ] 系统分层清晰 (Presentation/Domain/Infrastructure)
- [ ] 模块划分合理 (M1/M2/M3/M4 边界明确)
- [ ] 依赖关系无循环
- [ ] 关键路径有备选方案
- [ ] Vue 3 + Pinia 前端状态管理架构合理
- [ ] Tauri 桌面壳与 Web 职责分离明确

### 2.2 接口契约完整性

- [ ] 核心 API 接口已定义
- [ ] 数据模型已确定
- [ ] 错误码体系已规划
- [ ] WebSocket 消息格式已确定
- [ ] 前后端事件命名规范统一 (guidanceStore.js GUIDANCE_EVENTS)

### 2.3 任务分解合理性

- [ ] 任务依赖关系清晰
- [ ] 估算工时合理 (SMART)
- [ ] 关键路径任务已标识
- [ ] 并行任务可独立开发

### 2.4 风险识别

- [ ] 技术风险已识别并有对策
- [ ] 资源风险已评估
- [ ] 依赖外部系统的风险已标注
- [ ] Tauri 桌面环境特殊风险已评估

---

## 三、Interface Review Checklist (任务实现前)

### 3.1 REST API 接口

- [ ] HTTP Method 正确 (GET/POST/PUT/DELETE)
- [ ] Path 命名符合 REST 规范
- [ ] Request Body 结构确定
- [ ] Response 格式确定 (success/error)
- [ ] HTTP Status Code 正确 (200/201/400/401/403/409/500)
- [ ] 错误码定义完成

### 3.2 WebSocket 接口

- [ ] 连接认证方式确定
- [ ] 消息类型定义完成
- [ ] 心跳机制确定
- [ ] 断线重连策略确定
- [ ] Tauri WebView 中的 WebSocket 行为已验证

### 3.3 前后端接口一致性

- [ ] 前端 Mock 与后端实现约定一致
- [ ] 数据字段命名一致 (camelCase vs snake_case)
- [ ] 类型定义一致 (number vs string vs boolean)
- [ ] guidanceStore.js 事件与后端 GuidanceEvent 映射一致

### 3.4 Vue 3 组件接口

- [ ] Pinia Store 接口定义完整
- [ ] 组件 Props 类型定义完整
- [ ] 组件 Events (emit) 定义完整
- [ ] Composables 接口定义完整

---

## 四、Code Review Checklist (PR 时)

### 4.1 代码质量

- [ ] 代码符合 PEP8 (Python) / ESLint (JS) 规范
- [ ] 无 hardcoded 常量 (配置外置)
- [ ] 无冗余代码 (重复逻辑需抽象)
- [ ] 函数/类职责单一 (SRP)
- [ ] 变量/函数命名语义清晰

### 4.2 测试覆盖

- [ ] 核心逻辑有单元测试
- [ ] 边缘 case 有测试覆盖
- [ ] 测试可重复执行
- [ ] 测试之间无依赖
- [ ] Vue 3 组件有 Vitest 单元测试

### 4.3 安全性

- [ ] 用户输入有验证
- [ ] SQL/NoSQL 注入防护
- [ ] XSS 防护 (前端)
- [ ] 敏感信息不硬编码
- [ ] 权限检查正确
- [ ] Tauri IPC 权限控制正确

### 4.4 性能

- [ ] 无 N+1 查询问题
- [ ] 大数据量无内存泄漏
- [ ] 循环中有 yield/flush (流式处理)
- [ ] Vue 组件懒加载配置正确

### 4.5 文档同步

- [ ] 接口变更更新到 INTERFACE_CONTRACT.md
- [ ] 新组件更新到 COMPONENTS.md (如适用)
- [ ] guidanceStore 事件定义已同步
- [ ] README.md 或相关文档已更新

---

## 五、Integration Check Checklist (Sprint 结束)

### 5.1 模块间集成

- [ ] M1 (Admin) → M2 (Lifecycle) 集成正常
- [ ] M2 (Lifecycle) → M3 (Guidance) 集成正常
- [ ] 事件总线 (EventBus) 通信正常
- [ ] WebSocket 实时推送正常
- [ ] Tauri WebView 与前端通信正常
- [ ] Pinia Store 状态正确同步

### 5.2 功能验证

- [ ] 用户注册 → 引导触发 流程正常 (Vue 3 引导组件)
- [ ] 配额超限 → 拦截提示 流程正常
- [ ] 文件上传 → 实时更新 流程正常
- [ ] 团队创建 → 存储池分配 流程正常
- [ ] 引导状态 localStorage 持久化正常

### 5.3 回归测试

- [ ] 历史功能无退化
- [ ] API 契约测试通过
- [ ] WebSocket 契约测试通过
- [ ] E2E 关键路径测试通过

### 5.4 性能验证

- [ ] 页面加载时间 < 2s
- [ ] API 响应时间 < 500ms
- [ ] WebSocket 无延迟累积
- [ ] Tauri 桌面启动时间合理

### 5.5 Tauri 桌面壳验证

- [ ] 窗口创建和关闭正常
- [ ] 系统托盘功能正常 (如适用)
- [ ] 文件系统访问权限正确配置
- [ ] 桌面通知功能正常

---

## 六、紧急修复 Checkpoint

当 P0 bug 需要紧急修复时:

1. **快速评估** (15分钟)
   - 影响范围
   - 是否需要回滚
   - 临时解决方案

2. **修复后检查**
   - [ ] 影响功能验证
   - [ ] 相关模块回归测试
   - [ ] 通知相关团队
   - [ ] 24小时内复盘

---

## 七、文档更新要求

每次 Checkpoint 后必须更新:

| Checkpoint | 必更新文档 |
|------------|-----------|
| Architecture Review | TASK_BREAKDOWN.md, 版本日志 |
| Interface Review | INTERFACE_CONTRACT.md |
| Code Review | 代码注释 (如需要) |
| Integration Check | RTM.md (任务状态同步) |

---

## 八、G1-G8 完成状态确认

> 以下是当前已完成的里程碑，可作为 Integration Check 的参考基准

| 里程碑 | 内容 | 状态 | 说明 |
|--------|------|------|------|
| G1 | 项目初始化 | ~~~项目初始化~~~ ✅ | Vue 3 + Vite + Pinia + Tauri |
| G2 | Admin 控制台 | ~~~Admin 控制台~~~ ✅ | 实时数据 + WebSocket |
| G3 | 生命周期引擎 | ~~~生命周期引擎~~~ ✅ | 配额约束 + 边缘 case |
| G4 | 新手引导框架 | ~~~新手引导框架~~~ ✅ | guidanceStore.js |
| G5 | 前端引导组件 | ~~~前端引导组件~~~ ✅ | Vue 3 组件 |
| G6 | E2E 测试框架 | ~~~E2E 测试框架~~~ ✅ | Playwright |
| G7 | CI/CD 流水线 | ~~~CI/CD 流水线~~~ ✅ | GitHub Actions |
| G8 | 文档完善 | ~~~文档完善~~~ ✅ | RTM/RDM/RTM_TRACE |
| G9 | 实施中 | 🔄 | 持续集成与优化 |

---

## 九、版本历史

| 版本 | 日期 | 修改内容 |
|------|------|---------|
| 1.1 | 2026-05-05 | 更新为 Vue 3 + Pinia + Tauri 架构，新增 G1-G8 状态确认 |
| 1.0 | 2026-05-02 | 初始版本 |