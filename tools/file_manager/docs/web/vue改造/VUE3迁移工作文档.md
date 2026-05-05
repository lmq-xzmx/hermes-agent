# Vue 3 迁移工作文档

> **版本**: v7.1
> **更新日期**: 2026-05-05
> **方法论**: 自顶向下开发 (TOP_DOWN_DEVELOPMENT.md)
> **目标**: 将 app.html 迁移至 Vue 3 SPA
> **状态**: ✅ 迁移完成，进入维护阶段

---

## 1. 架构总览 (自顶向下)

### 1.1 分层架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Presentation Layer                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐  │
│  │LoginView│ │FileView │ │TeamView │ │SpaceView│ │ Others │ │Context │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                           Domain Layer                                   │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌─────────────┐ ┌───────────┐  │
│  │AuthStore │ │FileStore │ │TeamStore  │ │ SpaceStore  │ │ Guidance  │  │
│  └──────────┘ └──────────┘ └───────────┘ └─────────────┘ └───────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                       Infrastructure Layer                               │
│  ┌────────┐ ┌────────┐ ┌─────────┐ ┌────────────────┐ ┌─────────────┐   │
│  │Pinia   │ │Router  │ │API Client│ │TauriAdapter   │ │ WebSocket   │   │
│  └────────┘ └────────┘ └─────────┘ └────────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 当前状态

| 指标 | 数值 | 状态 |
|------|------|------|
| app.html 行数 | ~50 | ✅ 已废弃（仅作占位页面） |
| Vue 组件 | 12 个 | ✅ 已完成 |
| P0 组件 | 4/4 | ✅ 完成 |
| P1 功能 | 3/3 | ✅ 完成 |
| P2 功能 | 3/3 | ✅ 完成（含空状态引导完善） |
| 默认入口 | vue.html | ✅ 已切换 |
| Rust 代码 | 200 行 | ✅ G1 达标 (≤200行) |
| js/features/*.js | 已删除 | ✅ orphaned 模块清理 |
| 构建产物 | dist/ | ✅ 包含 vue.html, floating-vue.html |
| Tauri 主窗口 | vue.html | ✅ 已配置 |
| Tauri 浮窗 | floating-vue.html | ✅ 已配置 |

### 1.3 Tauri 窗口配置

```json
{
  "windows": [
    {
      "title": "Hermes File Manager",
      "url": "vue.html",      // Vue SPA 入口
      "label": "main"
    },
    {
      "title": "快捷浮窗",
      "url": "floating-vue.html",  // 浮窗 Vue 入口
      "label": "floating",
      "visible": false,
      "alwaysOnTop": true
    }
  ]
}
```

### 1.4 构建产物 (dist/)

```
dist/
├── vue.html           # Vue SPA 主入口
├── floating-vue.html  # 浮窗 Vue 入口
└── assets/
    ├── vue-*.js      # Vue 框架 bundle
    ├── api-*.js       # API 服务 bundle
    ├── style-*.css    # 样式
    └── floating-*.js  # 浮窗 bundle
```

### 1.5 Tauri 集成状态

| 功能 | 状态 | 说明 |
|------|------|------|
| show_floating_window | ✅ 已注册 | main.rs |
| hide_floating_window | ✅ 已注册 | main.rs |
| floating window close-to-hide | ✅ 已实现 | 关闭时隐藏而非退出 |
| useTauri/platformAdapter 对齐 | ✅ 已修复 | __TAURI_INVOKE__ 接口 |
| main window close-to-hide | ✅ 已实现 | 关闭时隐藏而非退出 |

### 1.6 质量门禁 (Contract-First)

```
代码合并前
    ↓
✅ 接口契约测试通过 (Contract Tests)
    ↓
✅ 单元测试通过 (>80% 覆盖率)
    ↓
✅ 组件测试通过 (>60% 覆盖率)
    ↓
✅ E2E 测试通过 (关键路径)
    ↓
✅ 可以合并
```

---

## 2. 接口契约定义 (Contract-First)

### 2.1 右键菜单接口

```typescript
// src/types/context-menu.ts

interface ContextMenuItem {
  id: 'open' | 'rename' | 'copy' | 'cut' | 'paste' | 'delete' | 'share' | 'info'
  label: string
  icon: string
  shortcut?: string
  danger?: boolean
  disabled?: boolean
  divider?: boolean
}

interface ContextMenuState {
  visible: boolean
  position: { x: number; y: number }
  target: FileItem | null
}
```

### 2.2 文件选择接口

```typescript
// src/types/file-selection.ts

interface FileSelectionState {
  selectedPaths: Set<string>
  hoveredPath: string | null
  dragRect: DOMRect | null
  isDragging: boolean
}
```

### 2.3 预览接口

```typescript
// src/types/preview.ts

interface PreviewState {
  visible: boolean
  currentPath: string
  files: FileItem[]
  currentIndex: number
  type: 'image' | 'markdown' | 'video' | 'audio' | 'pdf' | 'text' | 'other'
}
```

### 2.4 剪贴板接口

```typescript
// src/types/clipboard.ts

interface ClipboardState {
  mode: 'copy' | 'cut' | null
  paths: string[]
  timestamp: number
}
```

### 2.5 Workflow API

```typescript
// src/services/api.js - 已实现

getWorkflow(workflowId)           // GET /workflows/{id}
createWorkflow(spaceId, data)      // POST /spaces/{id}/workflows
updateWorkflow(workflowId, data)  // PATCH /workflows/{id}
deleteWorkflow(workflowId)         // DELETE /workflows/{id}
executeWorkflow(workflowId)       // POST /workflows/{id}/execute
```

### 2.6 Notebook API

```typescript
// src/services/api.js - 已实现

getNotebook(notebookId)           // GET /notebooks/{id}
createNotebook(spaceId, data)     // POST /spaces/{id}/notebooks
updateNotebook(notebookId, data)  // PATCH /notebooks/{id}
deleteNotebook(notebookId)        // DELETE /notebooks/{id}
duplicateNotebook(notebookId)     // POST /notebooks/{id}/duplicate
```

### 2.7 Team Credential API

```typescript
// src/services/api.js - 已实现

getTeamCredentials(teamId)           // GET /teams/{id}/credentials
createTeamCredential(teamId, data)   // POST /teams/{id}/credentials
deleteTeamCredential(teamId, credId) // DELETE /teams/{id}/credentials/{id}
```

---

## 3. 迁移任务分解

### 3.1 P0 - 核心功能（必须迁移）

| 任务 | 描述 | 依赖 | 工作量 | 状态 |
|------|------|------|--------|------|
| **P0-1** | 创建 `ContextMenu.vue` 组件 | 无 | 1h | ✅ 完成 |
| **P0-2** | 实现右键菜单逻辑 (`useContextMenu`) | ContextMenu | 2h | ✅ 完成 |
| **P0-3** | 框选功能 (`useDragSelection`) | FileView | 4h | ✅ 完成 |
| **P0-4** | 与 FileView 集成 | 上述全部 | 2h | ✅ 完成 |

### 3.2 P1 - 重要功能（应该迁移）

| 任务 | 描述 | 依赖 | 工作量 | 状态 |
|------|------|------|--------|------|
| **P1-1** | 剪贴板操作 (`useClipboard`) | 无 | 1h | ✅ 完成 |
| **P1-2** | Markdown 预览 (marked.js) | PreviewState | 3h | ✅ 完成 |
| **P1-3** | 预览导航 (左右箭头) | Preview | 2h | ✅ 完成 |

### 3.3 P2 - 辅助功能（可以迁移）

| 任务 | 描述 | 依赖 | 工作量 | 状态 |
|------|------|------|--------|------|
| **P2-1** | 键盘快捷键 (Ctrl+A/C/V/X) | 无 | 2h | ✅ 完成 |
| **P2-2** | 空状态引导完善 | FileView | 1h | ✅ 完成 |
| **P2-2a** | FileView集成spaceStore | FileView | 30m | ✅ 完成 |
| **P2-3** | 调试面板 DebugPanel | 无 | 1h | ✅ 完成 |

### 3.4 P3 - 次要功能（可选）

| 任务 | 描述 | 工作量 | 状态 |
|------|------|--------|------|
| **P3-1** | 文件筛选（文件名搜索） | 1h | ✅ 完成 |
| **P3-1a** | 文件标签/分类筛选 | 2h | ⚠️ 待后端支持 |
| **P3-2** | 高级搜索 | 4h | ⚠️ 待后端API |

---

## 4. 测试策略 (Contract-First)

### 4.0 契约测试 (Contract Tests)

**定义**: 验证前后端 API 接口契约一致性，100% API 覆盖

| 测试类型 | 位置 | 运行频率 | 状态 |
|---------|------|---------|------|
| API Contract | `tests/contract/api.test.js` | 每次提交 | ✅ |

**运行方式**: `npm test -- tests/contract/`

### 4.1 测试金字塔

```
                    ┌───────────┐
                    │    E2E    │  ← Playwright, 关键路径
                   ┌───────────┐┌───────────┐
                   │ Integration│  │ Contract  │
                  ┌───────────┐┌───────────┐┌───────────┐
                  │   Unit     ││   Unit     ││   Unit     │
                  └───────────┘└───────────┘└───────────┘
```

### 4.2 覆盖率目标

| 测试类型 | 目标 | 工具 |
|---------|------|------|
| 单元测试 | >80% | Vitest |
| 组件测试 | >60% | Vitest + Vue Test Utils |
| E2E 测试 | 关键路径 | Playwright |
| 契约测试 | 100% API | 自定义 |

---

## 5. app.html 清理计划

### 5.1 已清理的函数

| 函数分类 | 函数名 | 状态 |
|----------|--------|------|
| 框选函数 | `initDragSelection`, `onDragSelectionStart`, `onDragSelectionMove`, `updateDragSelectionRect`, `selectFilesInRect`, `onDragSelectionEnd` | ✅ 已移除 |
| 剪贴板函数 | `copyFilesToClipboard`, `pasteFromClipboard` | ✅ 已移除 |
| ContextMenu HTML | `id="contextMenu"` DOM 元素 | ✅ 已移除 (P0-1) |
| ContextMenu JS | `showContextMenu`, `hideContextMenu`, `handleContextMenuAction`, `initContextMenu` | ✅ 已移除 (P0-2) |
| selectedFiles 引用 | `selectedFiles.has(f.path)` 在 renderFilesGrid | ✅ 已移除 |
| 孤立函数 | `loadSpaceWorkflows`, `loadSpaceSettings`, `createWorkflow`, `deleteWorkflow`, `createNotebook`, `deleteNotebook` | 🔄 保留 (app.html 自调用, Vue SpaceView 已实现) |

### 5.2 待清理的函数

| 函数分类 | 函数名 | 建议操作 |
|----------|--------|---------|
| 已迁移 | `renderMarkdown` → `_renderMarkdown_placeholder` | ✅ 已完成 (PreviewModal) |
| 已迁移 | `viewNotebook`, `viewWorkflow` | ✅ 已完成 (SpaceView.vue) |
| 已迁移 | `executeWorkflow` | ✅ 已完成 (SpaceView.vue) |
| 已迁移 | `showTeamCredentials`, `createCred`, `deleteCred` | ✅ 已完成 (TeamView.vue) |
| 已迁移 | `loadSpaceSettings`, `loadSpaceWorkflows` 调用 | ✅ SpaceView.vue 已实现 |
| 孤立函数 | `createNotebook`, `deleteNotebook`, `createWorkflow`, `deleteWorkflow` | 🔄 保留供 app.html 内部使用 |

### 5.3 清理原则

1. **P0 功能完成后** - 移除对应的 app.html 函数
2. **保持兼容性** - Vue 功能完全可用前，不移除旧代码
3. **渐进式清理** - 每完成一个 P0/P1 任务，同步清理相关旧代码
4. **孤立函数** - 已无外部调用的函数保留在 app.html 供内部使用，不影响 Vue

---

## 6. 实施检查清单 (TOP_DOWN_DEVELOPMENT)

### 6.1 开发前 (Contract-First)
- [ ] 理解系统架构全貌 (Section 1)
- [ ] 明确模块边界和依赖关系
- [ ] 定义接口契约 (Section 2)
- [ ] 评估任务优先级 (Section 3)

### 6.2 开发中 (增量式实现)
- [ ] 遵循接口先行原则 (Contract-First)
- [ ] 增量实现，每步可运行
- [ ] 编写单元测试 (Vitest >80%)
- [ ] 契约测试通过

### 6.3 开发后 (质量门禁)
- [ ] 通过 Code Review
- [ ] 更新相关文档
- [ ] 运行 E2E 测试
- [ ] 验证性能指标

---

## 7. 相关文档

| 文档 | 说明 |
|------|------|
| `TOP_DOWN_DEVELOPMENT.md` | 自顶向下开发方法论 |
| `SYSTEM_ARCHITECTURE.md` | 系统架构 |

---

## 更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| **v7.1** | **2026-05-05** | **文档维护**: FEATURES.md 更新 Vue 组件结构；Apple Design 重构全部完成 (E01-E17) |
| **v7.0** | **2026-05-05** | **Tauri集成完成**: show/hide_floating_window命令添加；floating window close-to-hide；js/features/*.js orphaned模块删除；__TAURI_INVOKE__接口对齐；Rust 200行 ≤ 200行 ✅ |
| v6.2 | 2026-05-05 | **Rust 200行**: G1 100%达成；Tauri构建成功；Vue SPA与Tauri完整对接 |
| v6.1 | 2026-05-05 | **P3-1 完成**: Toolbar搜索框实现文件名实时筛选；P3-1a/P3-2 待后端API支持 |

---

## 8. app.html 函数分类总览

### 8.1 当前状态（已废弃旧统计）

> **注意**: app.html 已于 v6.2 转换为占位页面（原 4708 行 → 50 行）。旧函数统计表（72 函数/50 迁移）已过时，仅作历史参考。

| 指标 | 旧值 (v6.1) | 新值 (v7.0) | 说明 |
|------|-------------|-------------|------|
| app.html 行数 | 4,708 | 50 | ✅ 精简 99% |
| app.html 状态 | 正常页面 | 占位页面 | 仅显示架构说明 |
| js/features/*.js | 8个模块 | 已删除 | ✅ orphaned 清理 |
| 函数统计 | 72函数/50迁移 | 无效 | app.html 无业务逻辑 |

### 8.2 Vue 组件 vs app.html 函数映射（历史）

| app.html 函数 | Vue 组件 | Vue 函数 | 状态 |
|---------------|----------|----------|------|
| `loadFiles` | FileView.vue | `loadFiles()` | ✅ 已迁移 |
| `renderFiles` | FileView.vue | (响应式数据) | ✅ 已迁移 |
| `renderFilesGrid` | FileView.vue | (响应式数据) | ✅ 已迁移 |
| `getSelectedPaths` | FileView.vue | `selectedFiles` | ✅ 已迁移 |
| `toggleSelectAll` | FileView.vue | `toggleSelectAll()` | ✅ 已迁移 |
| `handleFileUpload` | FileView.vue | `handleFileUpload()` | ✅ 已迁移 |
| `deleteItem` | FileView.vue | `deleteItem()` | ✅ 已迁移 |
| `shareItem` | FileView.vue | `shareItem()` | ✅ 已迁移 |
| `openInFinder` | FileView.vue | `openInFinder()` |
| `createFolder` | FileView.vue | `createFolder()` |
| `createFile` | FileView.vue | `createFile()` |
| `loadTeams` | TeamView.vue | `loadTeams()` |
| `showCreateTeam` | TeamView.vue | `showCreateTeam()` |
| `createTeam` | TeamView.vue | `createTeam()` |
| `showTeamDetail` | TeamView.vue | `showTeamDetail()` |
| `deleteTeam` | TeamView.vue | `deleteTeam()` |
| `loadSpaces` | SpaceView.vue | `loadSpaces()` |
| `showSpaceDetail` | SpaceView.vue | `showSpaceDetail()` |
| `deleteSpace` | SpaceView.vue | `deleteSpace()` |
| `loadStorageContexts` | StoragePoolView.vue | `loadPools()` |

---

## 9. Phase 2：app.html 清理执行计划

### 9.1 清理策略

**原则**：验证一个功能 → 清理一组函数 → 更新文档

**顺序**：
1. 工具函数（`formatSize`, `formatDate`）- 无依赖，最安全
2. 文件操作函数 - FileView.vue 已完成
3. 团队管理函数 - TeamView.vue 已完成
4. 空间管理函数 - SpaceView.vue 已完成
5. 存储池函数 - StoragePoolView.vue 已完成

### 9.2 第一批清理目标

以下函数在 Vue 功能验证通过后，可以安全清理：

```javascript
// 文件操作（约 300 行）
loadFiles, renderFiles, renderFilesGrid, getSelectedPaths, toggleSelectAll,
updateSelectAllState, shareItems, handleFileUpload

// 团队管理（约 200 行）
loadTeams, renderMyTeams, renderAllTeams, showCreateTeam, createTeam,
showTeamDetail, deleteTeam, showTeamCredentials, createCred, deleteCred,
removeMember, joinTeam

// 空间管理（约 150 行）
loadSpaces, renderSpacesList, spaceCardHTML, showSpaceDetail, deleteSpace,
loadSpaceMembers, renderSpaceMembers, switchSpaceTab
```

### 9.3 验证检查清单

每次清理后，必须验证：

- [ ] 文件列表显示正常
- [ ] 文件上传功能正常
- [ ] 文件删除功能正常
- [ ] 文件分享功能正常
- [ ] 团队列表显示正常
- [ ] 空间列表显示正常
- [ ] 存储池显示正常
- [ ] 回收站功能正常

---

## 10. 相关文档

| 文档 | 说明 |
|------|------|
| `TOP_DOWN_DEVELOPMENT.md` | 自顶向下开发方法论 |
| `SYSTEM_ARCHITECTURE.md` | 系统架构 |
| `LIFECYCLE_CONSTRAINTS.md` | 生命周期约束 |
| `CONTRACT.md` | 接口契约定义 |
