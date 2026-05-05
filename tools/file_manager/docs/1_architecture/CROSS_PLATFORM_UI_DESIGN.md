# 跨平台文件管理器 UI/UE 设计规范

> **版本**: v1.2
> **创建日期**: 2026-05-03
> **更新日期**: 2026-05-05
> **来源**: Mac Finder vs Windows 文件管理器 UX 讨论 (2026-05-02)
> **状态**: ✅ 全部完成 (G1-G8 全部实现, GOALS.md v3.0)
>
> **更新说明 v1.2**: UI-1/4/7/8/9 已完成 ✅，UI-2/3 开发中 🔄，UI-5/6/10 待开始 ⏳

---

## 一、背景与目标

### 1.1 讨论背景

Web 端和 Tauri 桌面应用需要一套统一的交互方式，让用户感觉与 macOS Finder 和 Windows 文件管理器在视觉上类似、操作方式上接近。

### 1.2 设计目标

| 目标类型 | 具体描述 |
|---------|---------|
| **视觉相似** | 侧边栏、图标/列表视图、右键菜单等核心元素风格统一 |
| **操作接近** | 单击选中、拖拽移动、快捷键支持等交互习惯符合用户预期 |
| **跨平台一致** | Web、Tauri 共用同一套 UI 源码，保持体验统一 |

---

## 二、macOS Finder vs Windows 文件管理器 理念对比

### 2.1 核心哲学差异

| 维度 | macOS Finder | Windows 文件资源管理器 |
|------|-------------|----------------------|
| **设计理念** | 所见即所得，单窗口多标签 | 快速访问，多窗口并行 |
| **导航模型** | 侧边栏 + 路径栏 + Cover Flow | 左侧导航树 + 右上搜索 + 地址栏 |
| **选中机制** | 单击选中（需点击打开），与文档编辑一致 | 双击打开，经典 Windows 风格 |
| **视觉反馈** | 选中即编辑态，蓝色边框 | 图标/列表视图，蓝色方块选中 |
| **预览方式** | 空格键 Quick Look 预览 | 预览面板（可选） |

### 2.2 交互模型对比

```
macOS Finder:
┌─────────────────────────────────────────┐
│ [标题栏] Finder - 工作空间               │
├─────────┬───────────────────────────────┤
│ 侧边栏   │  文件网格/列表视图             │
│ - 个人空间│  ┌─────┐ ┌─────┐ ┌─────┐   │
│ - 共享   │  │ 📁  │ │ 📁  │ │ 📄  │   │
│ - 外接磁盘│  │文件1 │ │文件2 │ │文件3 │   │
│ - 回收站 │  └─────┘ └─────┘ └─────┘   │
│         │                               │
│         │  [详情面板] ← 可选             │
├─────────┴───────────────────────────────┤
│ [路径栏] 工作空间 > 文档 > 项目          │
└─────────────────────────────────────────┘

Windows 文件资源管理器:
┌─────────────────────────────────────────┐
│ [标题栏] 文件资源管理器                  │
├─────────┬───────────────────────────────┤
│ 导航窗格│  文件列表视图                  │
│ ▼ 桌面  │  ┌─────────────────────────────────┐
│ ▼ 文档  │  │ 📁 名称    │ 大小   │ 修改日期 ││
│   > 工作 │  │ 📁 文件1   │   -    │ 2026/5/3 ││
│ ▼ 下载  │  │ 📄 文件2   │ 1.2 MB │ 2026/5/2 ││
│ ▼ 回收站│  └─────────────────────────────────┘
├─────────┴───────────────────────────────┤
│ [地址栏] 此电脑 > 文档 > 工作           │
└─────────────────────────────────────────┘
```

### 2.3 用户习惯差异总结

| 操作 | macOS | Windows | 统一建议 |
|------|-------|---------|---------|
| 进入文件夹 | 单击 | 双击 | **单击** |
| 多选 | Cmd+点击 | Ctrl+点击 | Cmd/Ctrl+点击 |
| 范围选择 | Shift+点击 | Shift+点击 | Shift+点击 |
| 全选 | Cmd+A | Ctrl+A | Cmd/Ctrl+A |
| 重命名 | Enter | F2 / 双击名称 | **Enter** |
| 删除 | Cmd+Backspace | Delete | Cmd/Ctrl+Delete |
| 预览 | 空格 (Quick Look) | Alt+P | **空格** |
| 属性 | Cmd+I | Alt+Enter | **Alt/Cmd+I** |

---

## 三、跨平台实现可行性分析

### 3.1 功能分级

| 等级 | 功能 | Web | Tauri | 实现难度 |
|------|------|-----|-------|---------|
| **P0** | 侧边栏导航 | ✅ | ✅ | 低 |
| **P0** | 图标/列表视图切换 | ✅ | ✅ | 低 |
| **P0** | 单击选中文件 | ✅ | ✅ | 低 |
| **P0** | 右键上下文菜单 | ✅ | ✅ | 中 |
| **P1** | 工具栏（新建/上传/刷新） | ✅ | ✅ | 低 |
| **P1** | 面包屑路径导航 | ✅ | ✅ | 低 |
| **P1** | 拖拽选择（框选） | ⚠️ | ⚠️ | 中 |
| **P2** | 拖拽移动/复制文件 | ⚠️ | ⚠️ | 高 |
| **P2** | 空格预览（Quick Look） | ⚠️ | ⚠️ | 高 |
| **P3** | 多标签窗口 | ❌ | ⚠️ | 高 |
| **P3** | 窗口贴边/分屏 | ❌ | ⚠️ | 高 |

**图例**: ✅ 可行  ⚠️ 部分可行/复杂  ❌ 无法实现

### 3.2 技术限制详情

| 功能 | Web 限制 | Tauri 限制 | 解决方案 |
|------|---------|-----------|---------|
| 原生文件对话框 | 受浏览器安全限制 | 可调用系统 API | Tauri 使用 native dialog plugin |
| 文件系统直接访问 | 受沙盒限制 | 可用 fs plugin 绕过沙盒 | Web 通过 API，Tauri 直接访问 |
| 快捷键覆盖 | 浏览器快捷键冲突 | 需声明 shortcut capability | 拦截处理 + 平台适配 |
| 拖拽到外部应用 | 无法实现 | 无法实现 | 降级为"复制到剪贴板" |
| 系统图标渲染 | 系统图标不可用 | 系统图标不可用 | 使用 emoji 或自定义图标 |
| 原生通知 | 受限于浏览器 | 可用系统通知 | 统一使用 Web Notification API |

### 3.3 推荐的跨平台 UI 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    统一 Web UI 层                           │
│  ┌─────────────┬─────────────────────────┬───────────────┐  │
│  │   侧边栏     │      文件视图区域        │   详情面板    │  │
│  │  (Sidebar)  │   (Icon/List View)     │  (Preview)   │  │
│  └─────────────┴─────────────────────────┴───────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    统一交互逻辑层                            │
│  单击选中 │ 右键菜单 │ 拖拽处理 │ 快捷键 │ 视图切换         │
├─────────────────────────────────────────────────────────────┤
│                    统一 API 层                              │
│         localStorage │ fetch │ Tauri IPC Bridge            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐         ┌─────────────────┐          │
│  │   Web Browser    │         │  Tauri Desktop  │          │
│  │  (localhost:5173)│         │  (WebView)      │          │
│  └─────────────────┘         └─────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 SSOT (Single Source of Truth) 构建架构

**核心原则**: `web/dist` 是唯一构建产物，所有平台共用同一套代码。

```
web/
├── src/                    # Vue 3 源码 (SSOT)
│   ├── main.js            # Vue 应用入口
│   └── platformAdapter.js # 平台适配器
├── dist/                  # 唯一构建产物 ✅
│   ├── index.html
│   ├── vue.html           # Tauri 主窗口入口
│   └── ...
└── vue.html               # 开发模板入口

src-tauri/
└── tauri.conf.json
    └── frontendDist: "../web/dist"  # Tauri 引用 web/dist
```

**入口文件说明**:

| 文件 | 用途 | 说明 |
|------|------|------|
| `vue.html` | Tauri 主窗口 | 通过 tauri.conf.json 配置为默认窗口 |
| `floating-vue.html` | 浮窗入口 | 快捷浮窗，始终置顶 |
| `app.html` | 废弃 (50行占位符) | 已废弃，仅作占位符，不再用于生产 |
| `index.html` | 预留 | 备用入口 |

**平台适配器 (platformAdapter.js)**:

内联脚本，通过构建时变量 `__TAURI_MODE__`、`__API_BASE__` 区分运行环境：

```javascript
// Tauri 运行时
var TAURI_MODE = typeof __TAURI_MODE__ !== 'undefined' ? __TAURI_MODE__ : 'web';
var isTauriRuntime = typeof window.__TAURI__ !== 'undefined';
```

---

## 四、设计规范

### 4.1 布局规范

| 元素 | 最小宽度 | 最大宽度 | 高度 |
|------|---------|---------|------|
| 侧边栏 | 200px | 300px | 100% |
| 文件视图 | 400px | 自适应 | 自适应 |
| 工具栏 | 100% | - | 48px |
| 面包屑 | 100% | - | 36px |
| 状态栏 | 100% | - | 24px |

### 4.2 交互规范

#### 4.2.1 文件选中

```javascript
// 单击选中（Mac 风格）
fileElement.addEventListener('click', (e) => {
  if (!e.ctrlKey && !e.metaKey && !e.shiftKey) {
    clearSelection();
    selectFile(fileElement);
  }
});

// 多选（Cmd/Ctrl + 点击）
// 范围选（Shift + 点击）
```

#### 4.2.2 右键菜单

```javascript
// 统一右键菜单行为
document.addEventListener('contextmenu', (e) => {
  e.preventDefault();
  const clickedFile = findFileElement(e.target);
  if (clickedFile) {
    showContextMenu(e.clientX, e.clientY, clickedFile);
  }
});

// 菜单项
const menuItems = [
  { label: '打开', shortcut: 'Enter', action: 'open' },
  { label: '重命名', shortcut: 'F2', action: 'rename' },
  { label: '复制', shortcut: 'Cmd/Ctrl+C', action: 'copy' },
  { label: '移动到...', shortcut: '', action: 'move' },
  { label: '删除', shortcut: 'Cmd/Ctrl+Backspace', action: 'delete' },
  { separator: true },
  { label: '获取链接', shortcut: '', action: 'share' },
  { label: '显示详情', shortcut: 'Alt+I', action: 'info' },
];
```

### 4.3 视图模式

```javascript
const VIEW_MODES = {
  ICON: 'icon',    // 图标视图（类似 Finder 网格）
  LIST: 'list',    // 列表视图（类似 Windows 详情）
  COLUMN: 'column' // 分栏视图（类似 macOS Column View）
};
```

---

## 五、待开发任务

### 5.1 任务分解

| 任务 ID | 任务名称 | 优先级 | 预估工时 | 依赖 |
|---------|---------|--------|---------|------|
| UI-1 | 统一 app.html 和 index.html | P0 | 2h | 无 |
| UI-2 | 侧边栏组件化 | P0 | 4h | 无 |
| UI-3 | 图标/列表视图切换 | P0 | 4h | 无 |
| UI-4 | 单击选中逻辑 | P0 | 2h | 无 |
| UI-5 | 右键上下文菜单 | P1 | 4h | UI-4 |
| UI-6 | 拖拽框选功能 | P1 | 6h | UI-4 |
| UI-7 | 面包屑路径导航 | P1 | 2h | 无 |
| UI-8 | 空格预览功能 | P2 | 8h | UI-5 |
| UI-9 | 拖拽移动/复制 | P2 | 8h | UI-5 |
| UI-10 | 快捷键完整支持 | P1 | 4h | 无 |

### 5.2 Vue 3 实现状态 (2026-05-05 核实)

> **基准**: Vue 3 SPA + Vite + Pinia + Vue Router
> **架构**: Web优先 + Tauri壳模式 (GOALS.md v3.0)
> **入口**: vue.html (主窗口), floating-vue.html (浮窗)

| 任务 | Vue 3 实现状态 | 关键文件 | 完成度 |
|------|---------------|---------|--------|
| UI-1 | ✅ 已完成 | `vue.html` 为主入口 | 100% |
| UI-2 | ✅ 已完成 | `Sidebar.vue` (3129 bytes) | 100% |
| UI-3 | ✅ 已完成 | `FileView.vue` 视图切换 | 100% |
| UI-4 | ✅ 已完成 | `FileView.vue` 单击选中 | 100% |
| UI-5 | ✅ 已完成 | `FileView.vue` 右键菜单 | 100% |
| UI-6 | ⚠️ 部分实现 | `useDragSelection.js` 存在但未集成 | 60% |
| UI-7 | ✅ 已完成 | `FileView.vue` 面包屑 | 100% |
| UI-8 | ⚠️ 降级实现 | 点击预览面板替代空格预览 | 80% |
| UI-9 | ⚠️ 部分实现 | 拖拽选择已实现，拖拽移动未完成 | 50% |
| UI-10 | 🔄 开发中 | `useKeyboard.js` 等快捷键组件 | 80% |

### 5.3 Vue 3 组件清单

| 组件 | 路径 | 大小 | 状态 |
|------|------|------|------|
| LoginView | `views/LoginView.vue` | 8846 bytes | ✅ |
| Sidebar | `views/Sidebar.vue` | 3129 bytes | ✅ |
| MainLayout | `views/MainLayout.vue` | 1496 bytes | ✅ |
| FileView | `views/FileView.vue` | 28906 bytes | ⚠️ 过大待拆分 |
| SpaceView | `views/SpaceView.vue` | 31016 bytes | ⚠️ 过大待拆分 |
| TeamView | `views/TeamView.vue` | 14204 bytes | ✅ |
| StoragePoolView | `views/StoragePoolView.vue` | 15372 bytes | ✅ |
| KnowledgeView | `views/KnowledgeView.vue` | 8233 bytes | ⚠️ 功能待完善 |
| TrashView | `views/TrashView.vue` | 7132 bytes | ✅ |
| FloatingWindow | `views/FloatingWindow.vue` | 9397 bytes | ✅ |
| AdminDashboard | `views/AdminDashboard.vue` | 3699 bytes | ✅ |
| AdminTeams | `views/AdminTeams.vue` | 4802 bytes | ✅ |

### 5.4 进度追踪

| 任务 | 状态 | 完成度 |
|------|------|--------|
| UI-1 | ✅ 已完成 | 100% (app.html/index.html 废弃，vue.html 为主入口) |
| UI-2 | ✅ 已完成 | 100% (Vue 组件化完成) |
| UI-3 | ✅ 已完成 | 100% (视图切换已实现) |
| UI-4 | ✅ 已完成 | 100% (单击选中已实现) |
| UI-5 | ✅ 已完成 | 100% (右键上下文菜单已实现) |
| UI-6 | ⚠️ 部分实现 | 60% (useDragSelection 存在但未集成) |
| UI-7 | ✅ 已完成 | 100% (面包屑导航已实现) |
| UI-8 | ⚠️ 降级实现 | 80% (点击预览替代空格预览) |
| UI-9 | ⚠️ 部分实现 | 50% (拖拽选择可，拖拽移动未) |
| UI-10 | ✅ 已完成 | 100% (useKeyboardShortcuts.js + useClipboard.js 快捷键组件) |

---

## 六、结论

### 6.1 可行性总结

| 维度 | 评估 |
|------|------|
| **视觉相似** | ✅ 完全可行 - CSS/HTML 可完全复刻桌面文件管理器外观 |
| **操作接近** | ⚠️ 部分可行 - 核心交互（单击选中、右键菜单）可实现，拖拽到外部应用无法实现 |
| **跨平台一致** | ✅ 完全可行 - Web/Tauri 共用 UI 源码 |

### 6.2 核心建议

1. **采用 Mac Finder 交互模型**（单击选中）作为统一交互方式
2. **以 Web 技术为基础**，Tauri 作为原生包装层
3. **对无法实现的功能降级处理**（如拖拽到外部 → 降级为复制链接）
4. **优先实现 P0 功能**，后续迭代 P1/P2

### 6.3 降级策略

| 桌面功能 | Web 降级方案 |
|---------|-------------|
| 拖拽到桌面 | 提供"下载"按钮 |
| 原生文件对话框 | 使用 `<input type="file">` |
| Quick Look 预览 | 提供"预览"面板点击查看 |
| 拖拽到邮箱附件 | 提供"分享链接"功能 |

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0 | 2026-05-03 | 初始版本，基于 Mac Finder vs Windows 讨论结论 |
| 1.1 | 2026-05-04 | 新增 vue.html 入口说明、platformAdapter.js 架构 |
| 1.2 | 2026-05-05 | 更新 UI-5/6/7/8/9 实现状态，G9 开发中状态 |
