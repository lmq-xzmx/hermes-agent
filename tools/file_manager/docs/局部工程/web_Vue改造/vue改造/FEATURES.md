# Hermes File Manager - 功能清单

> Web 端访问地址: `http://localhost:5173/vue.html`
> Tauri 桌面端访问地址: `file:///Applications/Hermes File Manager.app/...`
> **架构**: Vue 3 SPA + Tauri 壳模式 (Web-First with Tauri Shell)
> **Vue 入口**: `vue.html` (默认)
> **浮窗入口**: `floating-vue.html`

---

## 目录

1. [侧边栏导航](#1-侧边栏导航)
2. [认证系统](#2-认证系统)
3. [文件视图](#3-文件视图)
4. [团队视图](#4-团队视图)
5. [空间视图](#5-空间视图)
6. [存储池视图](#6-存储池视图)
7. [知识视图](#7-知识视图)
8. [回收站视图](#8-回收站视图)
9. [引导系统](#9-引导系统)
10. [右键菜单](#10-右键菜单)
11. [调试功能](#11-调试功能)
12. [WebSocket 管理](#12-websocket-管理)
13. [Tauri 专有功能](#13-tauri-专有功能)

---

## 1. 侧边栏导航

6 个主视图，图标 + 功能：

| 视图 | 图标 | 功能 |
|------|------|------|
| 文件 | 📁 | 文件浏览、上传、下载、删除、分享 |
| 团队 | 👥 | 团队管理、创建、加入、邀请成员 |
| 空间 | 🚀 | 空间管理、成员管理、工作流、笔记本 |
| 存储池 | 💾 | 存储池创建、查看、配额管理 |
| 知识 | 🧠 | 知识库同步、搜索、LLM Wiki |
| 回收站 | 🗑️ | 文件恢复、清空 |

**底部**：
- 用户信息显示
- 退出登录按钮

---

## 2. 认证系统

| 功能 | UI 元素 | 说明 |
|------|---------|------|
| 用户登录 | `#loginForm` | 表单登录 |
| 用户注册 | `#registerForm` + `#showRegister` | 点击触发注册表单 |
| 自动登录 | localStorage | 保存 token，自动认证 |
| 记住密码 | `#rememberMe` | 复选框记住凭证 |
| 退出登录 | 侧边栏底部按钮 | 清除凭证，返回登录页 |
| 密码可见切换 | `togglePassword()` | 👁️ / 🙈 切换显示/隐藏 |

---

## 3. 文件视图

### 3.1 文件浏览

| 功能 | 说明 |
|------|------|
| 文件列表 | 列表视图显示文件 |
| 文件网格 | 网格视图显示文件 |
| 面包屑导航 | 显示当前路径，点击跳转 |
| 目录进入 | 点击目录进入 |
| 文件预览 | 点击文件预览 |
| 路径导航 | 前进/后退导航 |

### 3.2 文件操作

| 功能 | 说明 |
|------|------|
| 上传 | 拖拽或点击上传 (`#fileInput`) |
| 下载 | 点击文件下载 |
| 删除 | 删除文件到回收站 |
| 分享 | 生成分享链接 |
| 在 Finder 中显示 | Tauri 调用系统文件管理器 |
| 重命名 | 右键或 F2 |
| 复制/粘贴 | 复制文件路径，粘贴到目标目录 |

### 3.3 选择功能

| 功能 | 说明 |
|------|------|
| 单选 | 点击选中 |
| 多选 (Ctrl/Cmd) | 选中多个文件 |
| 框选 | 拖拽框选文件 |
| 全选 | Ctrl+A |
| 清除选择 | ESC |

### 3.4 视图切换

| 功能 | 说明 |
|------|------|
| 列表视图 | 详细信息列表 |
| 网格视图 | 图标网格展示 |
| 刷新 | 刷新文件列表 |

### 3.5 搜索

| 功能 | 说明 |
|------|------|
| 文件搜索 | 按文件名搜索 |

---

## 4. 团队视图

| 功能 | 说明 |
|------|------|
| 创建团队 | 创建新团队 |
| 加入团队 | 输入邀请码 (`#joinToken`) 加入 |
| 刷新 | 刷新团队列表 |
| 团队详情 | 查看团队信息 |
| 删除团队 | 删除团队 |
| 团队凭证 | 查看/创建/删除凭证 |
| 移除成员 | 从团队移除成员 |

---

## 5. 空间视图

| 功能 | 说明 |
|------|------|
| 创建空间 | 创建新的空间 |
| 成员管理 | 邀请、移除成员 |
| 工作流 | 查看、管理工作流 |
| 笔记本 | 笔记本列表 |
| 配额显示 | 显示空间配额使用情况 |
| 活动 | 查看空间活动日志 |
| 删除空间 | 删除空间 |
| 空间详情 | 查看空间详情 |
| 跨团队空间 | 查看/创建跨团队空间链接 |

---

## 6. 存储池视图

| 功能 | 说明 |
|------|------|
| 创建存储池 | 创建新的存储池 |
| 刷新 | 刷新存储池列表 |
| 清理存储池 | 清理存储池 |

---

## 7. 知识视图

| 功能 | 说明 |
|------|------|
| 同步到知识库 | 将文件同步到 LLM Wiki |
| 搜索知识库 | 搜索知识库内容 |
| 打开知识库 | 调用 `open_llm_wiki` 打开知识库 |
| 检查状态 | 检查知识库连接状态 |
| 同步设置 | 配置同步模式 |

---

## 8. 回收站视图

| 功能 | 说明 |
|------|------|
| 刷新 | 刷新回收站列表 |
| 恢复 | 恢复文件 |
| 永久删除 | 彻底删除文件 |
| 清空回收站 | 永久删除所有文件 |

---

## 9. 引导系统

### 9.1 引导事件类型

| 事件 | 触发时机 |
|------|----------|
| `USER_REGISTERED` | 用户注册成功 |
| `TEAM_JOINED` | 加入团队成功 |
| `FIRST_FILE_UPLOADED` | 首次上传文件 |
| `QUOTA_WARNING` | 配额警告 |
| `MEMBER_INVITED` | 成员邀请 |
| `WORKFLOW_EXECUTED` | 工作流执行 |
| `FIRST_NOTEBOOK_CREATED` | 首次创建笔记本 |

### 9.2 引导状态

| 功能 | 说明 |
|------|------|
| 触发引导 | `window.triggerGuidance()` |
| 忽略引导 | localStorage 持久化 (`hermes_guidance_{EVENT}_dismissed`) |
| 重置引导 | `guidance.resetGuidance()` |
| 显示次数限制 | 每个事件最多显示 3 次 |

---

## 10. 右键菜单

| 功能 | 说明 |
|------|------|
| 打开 | 打开文件/目录 |
| 重命名 | 重命名文件 |
| 复制 | 复制文件 |
| 粘贴 | 粘贴文件 |
| 删除 | 删除文件 |
| 在 Finder 中显示 | 显示文件位置 |

---

## 11. 调试功能

| 功能 | 说明 |
|------|------|
| Debug Panel | 可折叠调试面板 (`#debugPanel`) |
| debugLog | 记录调试日志 |
| 全局错误捕获 | `window.onerror` 捕获未处理错误 |
| 版本徽章 | 显示构建版本信息 |

---

## 12. WebSocket 管理

| 功能 | 说明 |
|------|------|
| 连接 WS | 连接管理后台 WebSocket |
| 断开 WS | 断开连接 |
| 发送消息 | 发送 WS 消息 |

---

## 13. Tauri 专有功能

> 注意：Web 端部分 Tauri 专有功能会 fallback 到 HTTP API 或显示路径。

| 功能 | 命令 | 说明 |
|------|------|------|
| 在 Finder 中显示 | `open_path_in_finder` | 调用系统文件管理器 |
| 打开知识库 | `open_llm_wiki` | 打开 LLM Wiki |
| 窗口切换 | `switch_window` | main/floating 切换 |
| 切换窗口显示 | `toggle_window` | 显示/隐藏窗口 |
| 获取系统状态 | `get_system_status` | 获取后端状态 |
| 获取构建信息 | `get_build_info` | 获取版本信息 |
| 系统托盘 | - | 菜单控制 (显示/隐藏浮窗、打开知识库、退出) |

### 13.1 浮窗功能

| 功能 | 说明 |
|------|------|
| 快速上传 | 浮窗中快速上传文件 |
| 搜索 | 浮窗中搜索文件 |

---

## UI 元素参考

> ⚠️ **注意**: 以下 UI 元素 ID 为旧架构 (app.html) 遗留，现已迁移至 Vue 3 SPA。Vue 组件通过 `src/` 目录下的 `.vue` 文件管理。

### Vue 组件结构

```
vue.html (主入口)
├── src/
│   ├── App.vue                      # 根组件
│   ├── main.js                      # Vue 应用入口
│   ├── router/                      # Vue Router 配置
│   ├── stores/                      # Pinia 状态管理
│   │   ├── authStore.js             # 认证状态
│   │   ├── fileStore.js             # 文件状态
│   │   ├── spaceStore.js            # 空间状态
│   │   └── ...
│   ├── views/                       # Vue 页面组件
│   │   ├── LoginView.vue            # 登录视图
│   │   ├── FileView.vue             # 文件视图
│   │   ├── TeamView.vue             # 团队视图
│   │   ├── SpaceView.vue            # 空间视图
│   │   ├── StoragePoolView.vue      # 存储池视图
│   │   ├── KnowledgeView.vue        # 知识视图
│   │   ├── TrashView.vue            # 回收站视图
│   │   └── Sidebar.vue              # 侧边栏
│   ├── components/                  # 可复用组件
│   │   ├── common/                  # 通用组件
│   │   │   ├── ButtonPrimary.vue    # 主按钮
│   │   │   ├── ButtonSecondary.vue  # 次要按钮
│   │   │   ├── SearchInput.vue     # 搜索输入框
│   │   │   └── ...
│   │   ├── PreviewModal.vue         # 预览弹窗
│   │   ├── DebugPanel.vue           # 调试面板
│   │   └── context-menu/
│   │       └── ContextMenu.vue     # 右键菜单
│   └── services/
│       └── api.js                  # API 服务层
```

### 视图路由

| 视图 | 路由 | Vue 组件 |
|------|------|---------|
| 文件 | `/files` 或 `/` | `FileView.vue` |
| 团队 | `/teams` | `TeamView.vue` |
| 空间 | `/spaces` | `SpaceView.vue` |
| 存储池 | `/pools` | `StoragePoolView.vue` |
| 知识 | `/knowledge` | `KnowledgeView.vue` |
| 回收站 | `/trash` | `TrashView.vue` |
| 登录 | `/login` | `LoginView.vue` |
| 浮窗 | `/floating-vue.html` | `FloatingWindow.vue` |

### 旧架构 UI 元素 (已废弃)

> ⚠️ 以下 ID 为旧架构遗留，现已迁移至 Vue 组件，仅作历史参考。

| 旧组件 ID | Vue 组件 | 说明 |
|-----------|----------|------|
| `#loginForm` | `LoginView.vue` | 登录表单已迁移 |
| `#registerForm` | `LoginView.vue` | 注册表单已迁移 |
| `#sidebar` | `Sidebar.vue` | 侧边栏已迁移 |
| `#fileList` / `#fileGrid` | `FileView.vue` | 文件列表已迁移 |
| `#breadcrumb` | `FileView.vue` 内部 | 面包屑已迁移 |
| `#debugPanel` | `DebugPanel.vue` | 调试面板已迁移 |
| `#modalOverlay` | 各 Modal 组件 | 模态框已迁移 |
| `#loadingOverlay` | 各视图组件 | 加载状态已迁移 |
| `#toastContainer` | GuidanceModal.vue | Toast 已集成到引导系统 |
| `#joinToken` | `TeamView.vue` | 加入团队 Token 已迁移 |
| `#fileInput` | `FileView.vue` 内部 | 文件上传已迁移 |

### 核心组件 API

#### SearchInput.vue
```vue
<SearchInput
  v-model="searchQuery"
  placeholder="搜索..."
  @search="onSearch"
  @clear="clearSearch"
/>
```

#### ButtonPrimary.vue
```vue
<ButtonPrimary @click="handleClick" :disabled="false">
  按钮文字
</ButtonPrimary>
```

#### ContextMenu.vue
```vue
<ContextMenu
  ref="contextMenuRef"
  :can-paste="canPaste"
  @open="onContextOpen"
  @delete="onContextDelete"
/>
```

#### PreviewModal.vue
```vue
<PreviewModal
  :visible="previewVisible"
  :file="previewFile"
  :files="previewableFiles"
  @close="closePreview"
/>
```

---

## 模块依赖（已废弃 Vanilla JS 架构）

> ⚠️ 以下模块依赖为 Vue 迁移前的旧架构，`app.html` 已废弃，仅保留 50 行占位页。
> 当前 Vue 3 SPA 架构使用 `vue.html` + `src/` 目录。

~~app.html~~ (已废弃，仅保留 50 行占位页)

### 新架构 (Vue 3 SPA)

```
vue.html (主入口)
├── src/
│   ├── main.js                # Vue 应用入口
│   ├── App.vue               # 根组件
│   ├── router/               # Vue Router 配置
│   ├── stores/               # Pinia 状态管理
│   ├── views/                # Vue 页面组件
│   ├── components/           # 可复用组件
│   ├── services/             # API 服务层
│   └── platformAdapter.js    # Tauri 平台适配器
```

~~app.html~~ (已废弃，仅保留 50 行占位页)
