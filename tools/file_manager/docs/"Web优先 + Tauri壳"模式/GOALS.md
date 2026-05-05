# Hermes File Manager - 目标体系

> **版本**: v3.0
> **更新日期**: 2026-05-05
> **模式**: Web优先 + Tauri壳模式 + Vue 3 SPA 迁移

---

## Vue 3 迁移状态

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 1-3 | ✅ 完成 | P0 组件（ContextMenu、DragSelection、useClipboard） |
| Phase 2 | ✅ 已完成 | app.html 清理，Vue 3 SPA 迁移完成 |
| 默认入口 | ✅ 已切换 | vue.html 作为主入口 |
| Tauri 集成 | ✅ 已配置 | tauri.conf.json 指向 vue.html |

---

## 架构原则（行业最佳实践）

| 原则 | 定义 | 目标映射 |
|------|------|---------|
| **最小权限原则** | Rust端只实现无法在Web端完成的功能（窗口管理、文件系统、系统托盘） | G1 |
| **职责分离原则** | Web做UI/业务，Tauri做窗口/打包，API做数据 | G2 |
| **单向依赖原则** | Web不直接依赖Tauri，通过抽象接口调用 | G1 |
| **配置驱动原则** | 通过tauri.conf.json声明式配置，避免Rust硬编码 | G8 |

### 层级定义

| 层级 | 职责 | 技术 |
|------|------|------|
| **产品交付层 (Web)** | UI渲染、业务逻辑、状态管理 | Vue/React + TypeScript |
| **Tauri 壳层** | 原生能力封装、窗口管理 | Rust + tauri.conf.json |
| **远程API层** | 数据持久化、业务计算 | REST/GraphQL |

### IPC机制说明

| 机制 | 说明 |
|------|------|
| **Commands/invoke** | 前端通过`invoke()`调用Rust函数 |
| **Events** | Rust主动推送事件到前端 |
| **window.__TAURI__** | 环境检测，区分Web/Tauri运行时的API_BASE路径 |

---

## 核心目标（必须达成）

| 编号 | 目标 | 描述 | 状态 |
|------|------|------|------|
| **G1** | Tauri 最低维护量 | Rust 代码 ≤ 200 行，仅做窗口管理和系统能力调用，无业务逻辑 | 实施中 |
| **G2** | Web 主导产品交付 | Vue 3 SPA 产品功能、UI/UE、交互逻辑在 Web 端开发和测试 | ✅ 已达成 |
| **G3** | SSOT | web/dist 是唯一构建产物，Vue SPA 和 Tauri 共用 | ✅ 已达成 |
| **G4** | 一次构建 | 前端只构建一次，同时用于 Web 和 Tauri | ✅ 已达成 |
| **G5** | API 统一 | 统一使用 `http://localhost:8080/api/v1`，无环境判断 | ✅ 已达成 |
| **G6** | 资源正确嵌入 | bundle.resources 将 web/dist 正确嵌入 app bundle | ✅ 已达成 |
| **G7** | 构建失败回滚 | 构建或验证失败时自动恢复上一可用版本 | ✅ 已达成 |
| **G8** | 窗口 URL 标准化 | 使用标准路径 `vue.html`，不用 `_up_` workaround | ✅ 已达成 |

---

## 工作模式（当前实践方式）

| 编号 | 模式 | 描述 |
|------|------|------|
| **WM1** | 跨端复用 | 一套代码覆盖桌面、移动、Web 三端 |
| **WM2** | 组件共享 | Web、Tauri、移动端共享 UI 组件库 |

---

## 问题追踪体系（与目标体系共存）

| 体系 | 用途 | 与目标关系 |
|------|------|-----------|
| **G1-G11** | 目标追踪 | 解决"要去哪" |
| **HIST-xxx** | 问题记录 | 解决"还剩哪些问题" |

- G1 目标解决后 → HIST 中对应问题标记为 ✅
- 新发现问题 → 优先判断是否影响 G1-G11，影响则补充目标
- 详见 `domain:Tauri&web.md` 历史问题章节

---

## 技术方法（与核心文档对齐）

| 方法 | 描述 | 对应目标 |
|------|------|---------|
| **platformAdapter 模式** | Web 通过统一抽象接口调用 Tauri 能力 | G1 |
| **Commands/Events IPC** | 前端 `invoke()` 调用 Rust，Rust 主动推送事件 | G1 |
| **条件编译** | Rust 通过 `#[cfg(target_os)]` 处理平台差异 | G1 |
| **跨端复用 (WM1)** | 一套代码覆盖桌面、移动、Web 三端 | G2 |
| **组件共享 (WM2)** | Web、Tauri、移动端共享 UI 组件库 | G2 |

---

## 长期目标（可选演进）

| 编号 | 目标 | 描述 | 前置条件 |
|------|------|------|----------|
| **G9** | Web 独立部署 | Web 可独立部署（Vercel/Netlify），不受 Tauri 影响 | 需要 CORS 配置 |
| **G10** | Tauri 按需打包 | 仅在有原生需求变更时重新打包 Tauri | G9 达成后 |
| **G11** | Tauri 自动更新 | 使用 updater 模块管理桌面端版本 | G10 达成后 |

---

## 部署方式说明

### 当前：嵌入模式

```
web/dist → 打包进 Tauri app bundle → /Applications/Hermes File Manager.app
```

- Tauri 启动时从 app bundle 本地加载 web/dist
- **内容与样式 = web/dist 完全一致**
- ✅ 离线可用
- ❌ Web 更新需要重新打包 Tauri

### 演进后：独立部署模式

```
Web → 部署到 Vercel/Netlify
Tauri → WebView 加载 https://your-app.vercel.app
```

- **内容与样式 = 远程 Web 完全一致**
- ✅ Web 更新无需重新打包 Tauri
- ❌ 需要网络连接

**无论哪种部署方式，Tauri 呈现的内容与 Web 一致。**

---

## 术语表

| 术语 | 定义 |
|------|------|
| **SSOT** | Single Source of Truth，web/dist 是唯一构建产物 |
| **Tauri 壳** | Tauri 仅作为桌面窗口包装，不承载业务逻辑 |
| **Web 优先** | 产品功能在 Web 端开发和测试，Tauri 仅做桌面集成 |
| **Commands/invoke** | Tauri IPC 调用机制，前端调用 Rust 函数 |
| **Events** | Tauri IPC 推送机制，Rust 主动推送事件到前端 |

---

## 相关文档

| 文档 | 说明 |
|------|------|
| `Tauri + Web 分离开发模式：以Web为中心的跨端架构实践.md` | 模式理论依据 |
| `README_BUILD.md` | 构建流程与操作指南 |
| `domain:Tauri&web.md` | 领域知识、问题记录 |

---

## 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-05-04 | 初始版本，建立目标体系 |
| 2.0 | 2026-05-04 | 补充架构原则、HIST-xxx共存说明、技术方法扩展 |
| 2.1 | 2026-05-04 | 补充层级定义、IPC机制说明，术语表增加Commands/Events |
| 2.2 | 2026-05-04 | 合并两版GOALS.md：术语统一，G8描述修正 |
| **2.3** | **2026-05-05** | **Vue 3 Phase 2 完成**：app.html 清理完成，E01-E17 全部完成，综合完成度 82% |

---

## Vue 3 SPA 最佳实践（补充）

> **版本**: v1.0
> **更新日期**: 2026-05-05
> **适用于**: Web优先 + Tauri壳模式下的 Vue 3 前端开发

### Vue 3 架构规范

| 规范 | 描述 | 对应原则 |
|------|------|---------|
| **VUE-001** | 组件采用 Composition API（`<script setup>`） | 可维护性 |
| **VUE-002** | 状态管理使用 Pinia，按领域拆分 Store | 可测试性 |
| **VUE-003** | 路由使用 Vue Router，模块化懒加载 | 性能优化 |
| **VUE-004** | 通过 Platform Adapter 抽象 Tauri/Web API | 跨端复用 |
| **VUE-005** | API 服务统一封装，错误处理标准化 | 契约先行 |

### 目录结构规范

```
src/
├── views/          # 页面组件（路由级别）
├── components/    # 公共组件
├── composables/   # 组合式函数（useXXX）
├── stores/        # Pinia 状态管理
├── services/      # API 服务封装
├── types/         # TypeScript 类型定义
├── platform/      # Platform Adapter（Tauri/Web 抽象）
└── router/        # 路由配置
```

### Platform Adapter 模式

```javascript
// platform/index.js
const platform = {
  api: { base: API_BASE, mode: TAURI_MODE },
  invoke: typeof __TAURI_INVOKE__ !== 'undefined' ? __TAURI_INVOKE__ : fetchApi,
  listen: typeof tauri !== 'undefined' ? tauri.listen : () => ({ unsubscribe: () => {} }),
}
```

### 组件设计原则

| 原则 | 描述 | 示例 |
|------|------|------|
| **单向数据流** | Props 向下传递，emit 向上传递 | `<FileCard :file="file" @select="handleSelect" />` |
| **Composables 封装** | 逻辑复用通过组合式函数 | `useContextMenu()`, `useClipboard()` |
| **Store 分离** | 按领域拆分，避免单一 store 膨胀 | `fileStore`, `teamStore`, `spaceStore` |
| **懒加载路由** | 非首屏组件使用 `defineAsyncComponent` | 路由懒加载 |

### SSOT 原则下的 Vue 开发

| 原则 | 描述 | 实现 |
|------|------|------|
| **单一构建源** | web/dist 是唯一构建产物 | `pnpm run build` → dist/ |
| **跨端复用** | 一套 Vue 代码跑在 Web 和 Tauri | Platform Adapter 抽象 |
| **契约先行** | API 接口先定义后实现 | types/ 定义接口契约 |

### 测试策略

| 层级 | 工具 | 覆盖率目标 |
|------|------|-----------|
| 单元测试 | Vitest | >80% |
| 组件测试 | Vitest + Vue Test Utils | >60% |
| E2E 测试 | Playwright | 关键路径 |
| 契约测试 | 自定义 | 100% API |
