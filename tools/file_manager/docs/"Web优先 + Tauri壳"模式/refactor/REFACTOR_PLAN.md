# app.html 重构方案

> **版本**: v1.0
> **日期**: 2026-05-04
> **目标**: 将 5876 行的 app.html 拆分为模块化结构

---

## 一、现状分析

### 1.1 文件规模

| 文件 | 行数 | 问题 |
|------|------|------|
| `web/app.html` | 5876 | 单一文件过大，难以维护 |

### 1.2 代码结构（按功能分段）

| 段落 | 行号范围 | 功能 | 函数数量 |
|------|---------|------|----------|
| **A. 核心初始化** | ~1827-2280 | API配置、认证、登录、版本标识 | ~20 |
| **B. 登录后设置** | ~2284-2638 | 空间选择、团队创建弹窗 | ~15 |
| **C. 侧边栏/视图模式** | ~2640-2710 | 视图切换、网格/列表渲染 | ~10 |
| **D. 文件操作** | ~2710-3376 | 上传、下载、删除、分享、预览 | ~35 |
| **E. 团队管理** | ~3377-3712 | 团队CRUD、成员管理 | ~15 |
| **F. 存储池** | ~3713-3890 | 存储池管理 | ~5 |
| **G. 知识/同步** | ~3890-4260 | Notebook、Workflow同步 | ~20 |
| **H. 空间管理** | ~4260-4750 | 空间CRUD、配额、设置 | ~30 |
| **I. 跨团队协作** | ~4751-4924 | 跨团队空间邀请 | ~10 |
| **J. Notebook函数** | ~4925-5490 | Notebook/Workflow详情 | ~40 |
| **K. 工具函数** | ~5559-end | 右键菜单、预览、拖拽选择 | ~35 |

**总计约**: ~225 个函数

---

## 二、重构目标模块

### 2.1 模块划分

```
web/
├── index.html              # 入口文件，仅保留 HTML 结构 + CSS
├── js/
│   ├── core/               # 核心模块
│   │   ├── config.js       # API配置、全局常量 (API_BASE, WS_BASE, TOKEN_KEY)
│   │   ├── init.js         # 应用初始化、入口点
│   │   ├── api.js          # HTTP请求封装 (api, apiUpload)
│   │   └── state.js        # 全局状态管理 (currentPath, currentSpaceId, token)
│   │
│   ├── auth/               # 认证模块
│   │   ├── auth.js         # 登录/注册/登出
│   │   ├── checkAuth.js    # 认证检查
│   │   └── wsAdmin.js      # WebSocket管理
│   │
│   ├── components/         # UI组件
│   │   ├── sidebar.js      # 侧边栏
│   │   ├── fileList.js     # 文件列表渲染（网格/列表）
│   │   ├── fileToolbar.js  # 文件工具栏
│   │   ├── breadcrumb.js   # 面包屑导航
│   │   ├── modal.js        # 弹窗管理
│   │   ├── toast.js        # 提示消息
│   │   ├── debug.js        # 调试面板
│   │   └── contextMenu.js  # 右键菜单
│   │
│   ├── features/           # 功能模块
│   │   ├── files.js        # 文件操作（上传/下载/删除）
│   │   ├── teams.js        # 团队管理
│   │   ├── storagePools.js # 存储池
│   │   ├── spaces.js      # 空间管理
│   │   ├── notebooks.js    # Notebook CRUD
│   │   ├── workflows.js    # Workflow CRUD
│   │   └── preview.js      # 文件预览
│   │
│   └── utils/              # 工具函数
│       ├── format.js       # formatSize, formatDate
│       ├── dragDrop.js     # 拖拽选择
│       └── clipboard.js    # 剪贴板操作
│
├── styles/
│   └── main.css            # 合并所有样式（从 app.html 提取）
│
└── dist/                   # 构建产物（Vite 输出）
```

### 2.2 模块依赖关系

```
config.js          ← 无依赖（基础配置）
state.js           ← config.js（使用 API_BASE 等常量）
api.js             ← config.js, state.js（使用 token）
init.js            ← core 所有模块（入口）
auth.js            ← api.js（使用 api 函数）
wsAdmin.js         ← api.js, state.js
sidebar.js         ← state.js, modal.js
fileList.js        ← state.js, api.js
...
```

---

## 三、实施步骤

### 第一阶段：代码提取（1-2天）

| 步骤 | 内容 | 工作量 |
|------|------|--------|
| 1.1 | 提取 CSS 到 `styles/main.css` | 2h |
| 1.2 | 创建 `js/core/config.js`（API_BASE, WS_BASE, TOKEN_KEY 等） | 1h |
| 1.3 | 创建 `js/core/state.js`（全局变量） | 1h |
| 1.4 | 创建 `js/core/api.js`（api 函数） | 1h |
| 1.5 | 创建 `js/utils/format.js`（formatSize, formatDate 等） | 0.5h |

### 第二阶段：组件拆分（2-3天）

| 步骤 | 内容 | 工作量 |
|------|------|--------|
| 2.1 | 创建 `js/components/modal.js` | 1h |
| 2.2 | 创建 `js/components/toast.js` | 0.5h |
| 2.3 | 创建 `js/components/breadcrumb.js` | 0.5h |
| 2.4 | 创建 `js/components/sidebar.js` | 1h |
| 2.5 | 创建 `js/components/fileList.js` | 2h |
| 2.6 | 创建 `js/components/contextMenu.js` | 1h |

### 第三阶段：功能模块拆分（3-5天）

| 步骤 | 内容 | 工作量 |
|------|------|--------|
| 3.1 | 创建 `js/auth/auth.js`（登录/注册/登出） | 2h |
| 3.2 | 创建 `js/auth/checkAuth.js` | 1h |
| 3.3 | 创建 `js/features/files.js` | 3h |
| 3.4 | 创建 `js/features/teams.js` | 2h |
| 3.5 | 创建 `js/features/spaces.js` | 3h |
| 3.6 | 创建 `js/features/notebooks.js` | 3h |
| 3.7 | 创建 `js/features/preview.js` | 2h |

### 第四阶段：整合与构建（1-2天）

| 步骤 | 内容 | 工作量 |
|------|------|--------|
| 4.1 | 创建 Vite 配置，支持多模块打包 | 2h |
| 4.2 | 创建 `index.html` 入口文件 | 1h |
| 4.3 | 修复模块间依赖问题 | 2h |
| 4.4 | 验证所有功能正常 | 2h |

---

## 四、技术方案

### 4.1 构建工具

**方案选择**: Vite（已有）
- 优势：快速HMR，ESM原生支持，配置简单
- 现状：项目已有 `vite.config.js`

### 4.2 模块格式

**方案选择**: ES Modules（原生）
```javascript
// config.js
export const API_BASE = window.API_BASE;

// state.js
import { API_BASE } from './config.js';
export let currentSpaceId = null;
```

### 4.3 状态管理

**方案选择**: 简化模块化（不用 Redux/Vuex）
```javascript
// state.js - 集中管理
export const state = {
  currentPath: '/',
  currentSpaceId: null,
  token: localStorage.getItem('hfm_token'),
  // ...其他状态
};
export function setState(key, value) { state[key] = value; }
```

### 4.4 样式处理

- 保持现有 CSS 结构（不变）
- 通过 Vite 导入 CSS 模块（可选）
- 后期可考虑 CSS-in-JS 或 Tailwind

---

## 五、验证计划

| 阶段 | 验证内容 | 方法 |
|------|---------|------|
| 第一阶段 | 基础功能正常 | 手动测试登录、上传 |
| 第二阶段 | UI组件正常 | 测试侧边栏、文件列表渲染 |
| 第三阶段 | 功能完整 | 测试所有 CRUD 操作 |
| 第四阶段 | 回归测试 | 对比重构前后的功能差异 |

---

## 六、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 模块间循环依赖 | 构建失败 | 合理规划依赖方向 |
| 全局变量分散 | 状态不一致 | 集中在 state.js 管理 |
| 函数名冲突 | 运行时错误 | 使用有前缀的命名（`files_`, `teams_`） |
| 构建产物增大 | 加载变慢 | 使用 Vite tree-shaking |

---

## 七、预期成果

| 指标 | 重构前 | 重构后 |
|------|-------|-------|
| app.html 行数 | 5876 | ~500（仅 HTML 模板） |
| JS 模块数 | 1 | ~20 个模块 |
| 单模块最大行数 | 5876 | ~300 |
| 可维护性 | 低 | 高 |
| 可测试性 | 低 | 高（模块可单独测试） |

---

## 八、注意事项

1. **渐进式重构** - 不要一次性重写，先拆分再合并
2. **保持功能一致** - 每拆分一个模块，验证功能正常
3. **Git 提交规范** - 每完成一个模块，提交一次
4. **文档更新** - 重构完成后更新相关文档

---

## 九、下一步行动

1. ✅ 确认方案
2. ✅ 创建 `web/js/core/` 目录结构
3. ✅ 从 `app.html` 提取 CSS 到 `styles/main.css`
4. ✅ 创建 `config.js` 和 `state.js`
5. ✅ 创建 `api.js`
6. ✅ 创建 `init.js`
7. ✅ 创建 components (modal, toast, loading, breadcrumb, sidebar)
8. ✅ 创建 features 模块 (files, teams, spaces, notebooks)
9. ✅ 创建 auth 模块 (auth.js, wsAdmin.js)
10. ✅ 创建 main.js 入口文件
11. ✅ 在 app.html 中导入 app.js 模块
12. ✅ 逐步替换 inline JS 为模块调用（大部分已完成，剩余少量复杂函数）
13. ✅ 完整回归测试