# Apple Design System 前端全面改造实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将所有前端组件改造为符合 Apple Design System 规范

**Architecture:** 增量式改造策略，每次1个组件，按优先级分3个阶段执行：
- Phase 1: 高频基础组件（功能不变）
- Phase 2: 业务页面（视觉一致）
- Phase 3: 问题组件（两者兼顾）

**Tech Stack:** Vue 3, CSS Variables, Apple Design System tokens

---

## 文件结构

### 改造范围

```
tools/file_manager/web/src/
├── components/
│   └── common/
│       ├── TextInput.vue      (Phase 1)
│       ├── Dropdown.vue       (Phase 1)
│       ├── Modal.vue          (Phase 1)
│       ├── SearchInput.vue    (Phase 1)
│       ├── Tabs.vue           (Phase 1)
│       └── Toast.vue          (Phase 1)
│   ├── FileContextMenu.vue    (Phase 3)
│   └── DebugPanel.vue         (Phase 3)
└── views/
    ├── LoginView.vue          (Phase 2)
    ├── FileView.vue           (Phase 2)
    └── Sidebar.vue            (Phase 2)
```

---

## Phase 1: 高频基础组件（功能不变）

### Task 1: TextInput.vue 改造

**Files:**
- Modify: `tools/file_manager/web/src/components/common/TextInput.vue`

**Current Issues:**
- 间距使用硬编码 `padding: 11px 15px` 而非 `var(--spacing-*)`

**Checklist:**

- [ ] **Step 1: 读取当前实现**

读取文件并确认需要修改的硬编码间距值

- [ ] **Step 2: 修改间距为 CSS 变量**

将 `padding: 11px 15px` 改为 `padding: var(--spacing-sm) var(--spacing-md)`

- [ ] **Step 3: 验证修改**

确认无其他硬编码值

- [ ] **Step 4: 提交**

```bash
git add tools/file_manager/web/src/components/common/TextInput.vue
git commit -m "refactor(TextInput): use spacing CSS variables per Apple Design"
```

---

### Task 2: Dropdown.vue 改造

**Files:**
- Modify: `tools/file_manager/web/src/components/common/Dropdown.vue`

**Current Issues:**
- 缺少字体变量

**Checklist:**

- [ ] **Step 1: 读取当前实现**

检查 Dropdown.vue 中的字体使用情况

- [ ] **Step 2: 添加字体变量**

确认使用 `var(--font-family-text)` 或 `var(--font-family-display)`

- [ ] **Step 3: 验证修改**

确认字体正确应用

- [ ] **Step 4: 提交**

```bash
git add tools/file_manager/web/src/components/common/Dropdown.vue
git commit -m "refactor(Dropdown): add font-family CSS variables per Apple Design"
```

---

### Task 3: Modal.vue 改造

**Files:**
- Modify: `tools/file_manager/web/src/components/common/Modal.vue`

**Current Issues:**
- 使用 `var(--shadow-lg)` 而非 `shadow-product`（阴影应仅限产品图）

**Checklist:**

- [ ] **Step 1: 读取当前实现**

检查 Modal.vue 中的阴影使用

- [ ] **Step 2: 移除阴影**

Modal 不应使用任何阴影（Apple Design 阴影仅限产品图）

- [ ] **Step 3: 验证修改**

确认无阴影使用

- [ ] **Step 4: 提交**

```bash
git add tools/file_manager/web/src/components/common/Modal.vue
git commit -m "refactor(Modal): remove shadow per Apple Design spec"
```

---

### Task 4: SearchInput.vue 改造

**Files:**
- Modify: `tools/file_manager/web/src/components/common/SearchInput.vue`

**Checklist:**

- [ ] **Step 1: 读取当前实现**

- [ ] **Step 2: 逐项检查**

按检查清单验证：
- 颜色：使用 `var(--color-*)`
- 字体：使用 `var(--font-family-text)`
- 间距：使用 `var(--spacing-*)`
- 圆角：使用 `var(--radius-pill)`
- 无硬编码 fallback

- [ ] **Step 3: 修复发现的问题**

- [ ] **Step 4: 提交**

```bash
git add tools/file_manager/web/src/components/common/SearchInput.vue
git commit -m "refactor(SearchInput): align with Apple Design CSS variables"
```

---

### Task 5: Tabs.vue 改造

**Files:**
- Modify: `tools/file_manager/web/src/components/common/Tabs.vue`

**Checklist:**

- [ ] **Step 1: 读取当前实现**

- [ ] **Step 2: 逐项检查**

按检查清单验证所有 CSS 变量

- [ ] **Step 3: 修复发现的问题**

- [ ] **Step 4: 提交**

```bash
git add tools/file_manager/web/src/components/common/Tabs.vue
git commit -m "refactor(Tabs): align with Apple Design CSS variables"
```

---

### Task 6: Toast.vue 改造

**Files:**
- Modify: `tools/file_manager/web/src/components/common/Toast.vue`

**Checklist:**

- [ ] **Step 1: 读取当前实现**

- [ ] **Step 2: 逐项检查**

按检查清单验证所有 CSS 变量

- [ ] **Step 3: 修复发现的问题**

- [ ] **Step 4: 提交**

```bash
git add tools/file_manager/web/src/components/common/Toast.vue
git commit -m "refactor(Toast): align with Apple Design CSS variables"
```

---

## Phase 2: 业务页面（视觉一致）

### Task 7: LoginView.vue 改造

**Files:**
- Modify: `tools/file_manager/web/src/views/LoginView.vue`

**Current Issues:**
- 大量 `var(--color-xxx, #hardcode)` fallback 模式
- 非标准字体变量

**Checklist:**

- [ ] **Step 1: 读取当前实现**

- [ ] **Step 2: 去除所有 fallback 模式**

将 `var(--xxx, #hardcode)` 改为纯 `var(--xxx)`

- [ ] **Step 3: 统一字体变量**

将 `var(--text-display-md)` 等改为标准 `var(--font-family-display)`

- [ ] **Step 4: 统一间距/圆角变量**

去除所有硬编码 fallback

- [ ] **Step 5: 浏览器验证**

启动开发服务器，验证视觉效果

- [ ] **Step 6: 提交**

```bash
git add tools/file_manager/web/src/views/LoginView.vue
git commit -m "refactor(LoginView): full Apple Design CSS variable alignment"
```

---

### Task 8: FileView.vue 改造

**Files:**
- Modify: `tools/file_manager/web/src/views/FileView.vue`

**Current Issues:**
- 大量 fallback 模式
- 非标准字体变量

**Checklist:**

- [ ] **Step 1: 读取当前实现**

- [ ] **Step 2: 批量去除 fallback**

逐个去除 `var(--xxx, #hardcode)` 中的 hardcode

- [ ] **Step 3: 统一字体变量**

- [ ] **Step 4: 统一间距/圆角变量**

- [ ] **Step 5: 浏览器验证**

- [ ] **Step 6: 提交**

```bash
git add tools/file_manager/web/src/views/FileView.vue
git commit -m "refactor(FileView): full Apple Design CSS variable alignment"
```

---

### Task 9: Sidebar.vue 改造

**Files:**
- Modify: `tools/file_manager/web/src/views/Sidebar.vue`

**Checklist:**

- [ ] **Step 1: 读取当前实现**

- [ ] **Step 2: 逐项检查**

按检查清单验证所有 CSS 变量

- [ ] **Step 3: 修复发现的问题**

- [ ] **Step 4: 浏览器验证**

- [ ] **Step 5: 提交**

```bash
git add tools/file_manager/web/src/views/Sidebar.vue
git commit -m "refactor(Sidebar): align with Apple Design CSS variables"
```

---

## Phase 3: 问题组件（两者兼顾）

### Task 10: FileContextMenu.vue 改造

**Files:**
- Modify: `tools/file_manager/web/src/components/FileContextMenu.vue`

**Current Issues:**
- 字体变量使用 `var(--font-body)` 而非标准变量
- 大量 CSS 变量使用 hardcode fallback

**Checklist:**

- [ ] **Step 1: 读取当前实现**

- [ ] **Step 2: 修复字体变量**

将 `var(--font-body)` 改为 `var(--font-family-text)`

- [ ] **Step 3: 去除 fallback**

去除所有 `var(--xxx, #hardcode)` 中的 hardcode

- [ ] **Step 4: 功能验证**

确认右键菜单功能正常

- [ ] **Step 5: 提交**

```bash
git add tools/file_manager/web/src/components/FileContextMenu.vue
git commit -m "refactor(FileContextMenu): fix font variables and remove fallbacks"
```

---

### Task 11: DebugPanel.vue 改造

**Files:**
- Modify: `tools/file_manager/web/src/components/DebugPanel.vue`

**Current Issues:**
- 字体变量使用 `var(--font-body)` 而非标准变量
- 调试按钮缺少 active 状态

**Checklist:**

- [ ] **Step 1: 读取当前实现**

- [ ] **Step 2: 修复字体变量**

将 `var(--font-body)` 改为 `var(--font-family-text)`

- [ ] **Step 3: 添加按钮 active 状态**

添加 `.debug-btn:active { transform: scale(0.95); }`

- [ ] **Step 4: 去除 fallback**

- [ ] **Step 5: 提交**

```bash
git add tools/file_manager/web/src/components/DebugPanel.vue
git commit -m "refactor(DebugPanel): fix font variables and add active state"
```

---

## 改造检查清单汇总

每个组件改造完成后，确认以下检查项：

| 检查项 | 规范 |
|--------|------|
| 颜色 | 全部使用 `var(--color-*)`，无硬编码 |
| 字体 | 使用 `var(--font-family-text)` 或 `var(--font-family-display)` |
| 间距 | 使用 `var(--spacing-*)` |
| 圆角 | 使用 `var(--radius-*)` |
| 阴影 | 仅产品图使用 `var(--shadow-product)` |
| 按钮 active | `transform: scale(0.95)` |
| fallback | 禁止 `var(--xxx, #hardcode)` 模式 |

---

## 变量映射参考

### 字体

| 旧 | 新 |
|----|----|
| `var(--font-body)` | `var(--font-family-text)` |
| `var(--font-display)` | `var(--font-family-display)` |
| `var(--text-body)` | `var(--font-family-text)` |
| `var(--text-display-md)` | `var(--font-family-display)` |

### 间距

| 值 | 变量 |
|----|------|
| 4px | `var(--spacing-xxs)` |
| 8px | `var(--spacing-xs)` |
| 12px | `var(--spacing-sm)` |
| 17px | `var(--spacing-md)` |
| 24px | `var(--spacing-lg)` |
| 32px | `var(--spacing-xl)` |
| 48px | `var(--spacing-xxl)` |
| 80px | `var(--spacing-section)` |

### 圆角

| 值 | 变量 |
|----|------|
| 0px | `var(--radius-none)` |
| 5px | `var(--radius-xs)` |
| 8px | `var(--radius-sm)` |
| 11px | `var(--radius-md)` |
| 18px | `var(--radius-lg)` |
| 9999px | `var(--radius-pill)` / `var(--radius-full)` |

---

## 相关文档

- 设计规范: `docs/superpowers/specs/2026-05-05-apple-design-frontend-refactor-design.md`
- 令牌定义: `tools/file_manager/web/src/assets/tokens.css`
- Apple Design: `DESIGN.md`
