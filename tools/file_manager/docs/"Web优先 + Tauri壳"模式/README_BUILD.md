# Hermes File Manager 构建指南

> **版本**: v27.0
> **更新日期**: 2026-05-05
> **设计原则**: Tauri 壳最低维护，Vue 3 SPA 主导产品交付
> **术语标准**: GOALS.md v3.0
> **事实**: Rust 代码 200 行 ✅ (G1)，Vue SPA 默认入口 vue.html ✅ (G8)
> **Vue 迁移**: app.html 已废弃（50行占位页），vue.html + floating-vue.html 为 Tauri 入口
> **里程碑**: G1-G8 全部达成，综合完成度 92% (仅剩 TASK-012)

---

## 术语表 (与 GOALS.md v3.0 对齐)

| 术语 | 定义 | 状态 |
|------|------|------|
| **SSOT** | Single Source of Truth，web/dist 是唯一构建产物 | ✅ 已达成 |
| **Tauri 壳** | Tauri 仅作为桌面窗口包装，不承载业务逻辑 | ✅ 已实施 |
| **Web 优先** | 产品功能在 Web 端开发和测试，Tauri 仅做桌面集成 | ✅ 已实施 |
| **嵌入模式** | 当前部署模式：web/dist 打包进 Tauri app bundle | ✅ 已实施 |
| **独立部署模式** | 演进后部署模式：Web 部署到 Vercel/Netlify | 规划中 |
| **G1-G11** | 目标体系，与 HIST-xxx 问题体系共存 | 实施中 |

---

## 快速命令

> **注意**: 推荐使用 `pnpm` 替代 `npm`，避免 rollup 原生模块问题。

| 命令 | 触发语言 | 说明 |
|------|---------|------|
| `pnpm run dev` | "开发" | 启动 Vite dev server (Web 调试) |
| `./scripts/build.sh` | "重新构建并重启" | 前端构建 + Tauri Release 打包 + 安装 |
| `./scripts/start-debug.sh` | "启动 Debug 版本" | Debug 模式运行（开发调试用）|

---

## 一、架构原则

```
┌─────────────────────────────────────────────────────────────┐
│                        Hermes File Manager                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐     ┌─────────────────────────────────┐   │
│  │   Web 前端   │ ←── │   产品交付层 (Vite + Vue)        │   │
│  │  (src/web)  │     │   - pnpm run dev (开发)          │   │
│  │             │     │   - pnpm run build (构建)        │   │
│  └──────┬──────┘     └─────────────────────────────────┘   │
│         │ SSOT 单一构建源                                    │
│         ↓                                                    │
│  ┌─────────────┐     ┌─────────────────────────────────┐   │
│  │ Tauri 壳    │ ←── │   桌面包装层 (最低维护)          │   │
│  │  (src-tauri)│     │   - cargo tauri build         │   │
│  │  ✅ 200行   │     │   - 仅做桌面窗口包装             │   │
│  └─────────────┘     └─────────────────────────────────┘   │
│  ┌─────────────┐     ┌─────────────────────────────────┐   │
│  │  Python API │ ←── │   后端服务层                     │   │
│  │ (localhost: │     │   - FastAPI (server.py)         │   │
│  │   8080)    │     │   - 独立部署                    │   │
│  └─────────────┘     └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 核心原则 (G1-G8)

| 原则 | 说明 | 目标 | 状态 |
|------|------|------|------|
| **Tauri 壳最低维护 (G1)** | Rust 代码 ≤ 200 行，无业务逻辑 | ✅ 已达成 | 200行 = 200行目标 ✅ |
| **Web 主导产品交付 (G2)** | UI/UE/交互逻辑在 Web 端开发和测试 | ✅ 已达成 | ✅ |
| **SSOT (G3)** | web/dist 是唯一构建产物 | ✅ 已达成 | ✅ |
| **一次构建 (G4)** | 前端只构建一次，Web 和 Tauri 共用 | ✅ 已达成 | ✅ |
| **API 统一 (G5)** | http://localhost:8080/api/v1 | ✅ 已达成 | ✅ |
| **资源正确嵌入 (G6)** | bundle 正确打包 web/dist | ✅ 已达成 | ✅ |
| **构建失败回滚 (G7)** | 失败时自动恢复上一版本 | ✅ 已达成 | ✅ |
| **窗口 URL 标准化 (G8)** | 使用标准路径 vue.html | ✅ 已达成 | Vue SPA 为默认入口 |

---

## 二、构建输出

### 2.1 dist 目录结构

```
dist/
├── vue.html           (4.8KB) - Vue SPA 主入口
├── floating-vue.html  (4.7KB) - 浮窗入口
└── assets/
    ├── vue-*.js       (~119KB) - Vue 框架
    ├── vue-vendor-*.js (~107KB) - Vue vendor
    ├── api-*.js         (~6KB) - API 服务
    ├── marked-*.js     (~42KB) - Markdown 解析
    └── echarts-*.js  (~1.1MB) - 图表库
```

### 2.2 构建产物大小

| 产物 | 大小 | 说明 |
|------|------|------|
| vue.html | 4.8 KB | Vue SPA 入口 |
| floating-vue.html | 4.7 KB | 浮窗入口 |
| dist 总计 | **1.4 MB** | 包含 echarts |

---

## 三、TASK-009 CI/CD 自动化实施方案

### 3.1 目标

实现 GitHub Actions 自动化构建和发布流水线

### 3.2 实施步骤

1. **创建 GitHub Actions 目录**
```bash
mkdir -p .github/workflows
```

2. **创建工作流文件** `.github/workflows/build.yml`
```yaml
name: Build & Release

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: macos-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Install dependencies
        run: |
          cd web && pnpm install && cd ..
          cargo fetch

      - name: Build frontend
        run: |
          cd web && pnpm run build

      - name: Verify bundle
        run: ./scripts/verify-bundle.sh

      - name: Build Tauri
        run: cargo tauri build

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: Hermes-File-Manager
          path: src-tauri/target/release/bundle/macos/*.app
```

---

## 四、验证命令

```bash
# 1. Rust 代码行数
wc -l src-tauri/src/main.rs
# 目标: ≤ 200 行
# 当前: 200 行 ✅

# 2. 前端构建（推荐使用 pnpm）
cd web && pnpm run build

# chunk 大小验证
ls -lh dist/assets/*.js
# 预期:
# vue-vendor:  ~107 KB ✅
# vue:         ~119 KB ✅
# echarts:   ~1,119 KB ⚠️ (echarts 库本身)
# marked:      ~42 KB ✅
# api:          ~6 KB ✅

# 3. Bundle 验证
./scripts/verify-bundle.sh

# 4. Tauri 构建
cargo tauri build
```

---

## 五、目录结构

```
tools/file_manager/
├── web/                      # 产品交付层 (SSOT)
│   ├── src/                  # Vue 组件源码
│   │   ├── views/           # Vue 页面组件
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── services/        # API 服务
│   │   └── platformAdapter.js # Tauri 平台适配器
│   ├── dist/                 # Vite 构建产物 ← 唯一构建输出
│   ├── vite.config.js        # Vite 配置 ✅
│   └── tests/contract/       # 契约测试 ✅
│
├── src-tauri/                # Tauri 壳层 (最低维护)
│   ├── src/main.rs          # Rust 入口 ✅ TASK-001 (200行)
│   ├── tauri.conf.json      # Tauri 配置 ✅
│   └── target/             # 构建产物
│
├── scripts/                  # 构建脚本
│   ├── build.sh             # Release 构建脚本 ✅ TASK-004
│   ├── start-debug.sh       # Debug 构建脚本
│   └── verify-bundle.sh      # Bundle 验证 ✅ TASK-005
│
├── docs/
│   ├── 「Web优先 + Tauri壳」模式/
│   │   ├── GOALS.md              # 目标体系 v3.0
│   │   ├── domain:Tauri&web.md   # 领域知识 v10.0
│   │   ├── BUILD_PRACTICE_ANALYSIS.md  # 差距分析 v5.0
│   │   ├── README_BUILD.md       # 本文档 v27.0
│   │   ├── rdm/                  # 需求依赖矩阵 v13.0
│   │   ├── rtm/                  # 需求跟踪矩阵 v13.0
│   │   └── tasks/                # 任务清单 v15.0
│   └── adr/                      # ADR 文档 ✅ TASK-010
│
└── .github/workflows/         # CI/CD 📋 TASK-009
```

---

## 六、相关文档

| 文档 | 说明 |
|------|------|
| `GOALS.md` | 目标体系 (G1-G11)，术语标准 v3.0 |
| `domain:Tauri&web.md` | 领域知识、问题记录 v10.0 |
| `BUILD_PRACTICE_ANALYSIS.md` | 构建实践差距分析 v5.0 |
| `rdm/RDM_Requirements_Dependency_Matrix.md` | 需求依赖矩阵 v13.0 |
| `rtm/RTM.md` | 需求跟踪矩阵 v13.0 |
| `tasks/TODO.md` | 重构待办任务清单 v15.0 |
| `TOP_DOWN_DEVELOPMENT.md` | 自顶向下开发方法论 |

---

## 变更记录

| 日期 | 变更 |
|------|------|
| 2026-05-05 | **v27.0** - 构建优化：Vite配置移除app.html入口，dist精简至1.4MB |
| 2026-05-05 | **v26.0** - G1-G8 全部达成，综合完成度 73% |
| 2026-05-05 | v25.0 - Vue 3 迁移完成：app.html 废弃（50行），vue.html/floating-vue.html 为入口，Rust 200行 |
| 2026-05-05 | v25.0 - 构建优化完成（chunk 分割），pnpm 替代 npm |
| 2026-05-05 | v23.0 - Vue 3 SPA (vue.html) 已作为默认入口，G8 状态更新 |
| 2026-05-04 | v22.0 - 12/12 任务全部完成，TASK-009 CI/CD 已实施 |
| 2026-05-04 | v20.0 - Rust 192行，TASK-006/007 状态更新 |
| 2026-05-04 | v19.0 - Rust 169行全部完成，仅剩 TASK-009 CI/CD 规划中 |
| 2026-05-04 | v18.0 - 对齐代码现状：Rust 217行，TASK-003/004 已完成 |
| 2026-05-04 | v15.0 - 更新 HIST-016 状态为规划中，对齐 TODO.md |
| 2026-05-04 | v13.0 - 完善 TASK-003~012 详细实施方案 |
| 2026-05-04 | v11.0 - 对齐 tasks/TODO.md v8.0 |
| 2026-05-04 | v10.0 - 新增 10 人并行分组 |
| 2026-05-04 | v9.0 - 对齐 GOALS.md v2.2 |
| 2026-05-04 | v5.0 - 初始文档 |

| 2026-05-05 | v28.0 - 更新综合完成度 92%，对齐 TODO.md v16.0 |
