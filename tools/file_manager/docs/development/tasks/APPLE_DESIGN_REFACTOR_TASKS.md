# Hermes File Manager 前端 Apple Design 改造任务书

> **版本**: 1.2
> **创建日期**: 2026-05-05
> **更新日期**: 2026-05-05
> **设计基准**: DESIGN.md (Apple Design System)
> **改造范围**: tools/file_manager/web/src/
> **完成进度**: 10/10 任务已完成

---

## 一、改造目标

基于 `DESIGN.md` Apple Design System 全面重构前端 UI，实现：
- 统一的设计语言 (SF Pro Typography, Action Blue #0066cc)
- 摄影优先的视觉呈现
- Apple 标志性的 pill 按钮、18px 圆角卡片
- 深浅交替的 tile 布局节奏

---

## 二、现状分析

| 类型 | 数量 | 说明 |
|------|------|------|
| 视图 (Views) | 17 | Login, File, Team, Space, StoragePool, Knowledge, Trash, Admin... |
| 组件 (Components) | 19 | Admin, Approval, Common, ContextMenu, Lifecycle |
| 设计系统 | 无 | 缺乏统一的设计 Token |

---

## 三、任务总览

| 任务编号 | 任务名称 | 优先级 | 预估工时 | 依赖 | 状态 |
|---------|---------|--------|----------|------|------|
| TASK-D01 | 创建 Design Tokens CSS | P0 | 4h | - | ✅ 已完成 |
| TASK-D02 | 构建 Button 组件 | P0 | 6h | TASK-D01 | ✅ 已完成 |
| TASK-D03 | 构建 Card 组件 | P0 | 6h | TASK-D01 | ✅ 已完成 |
| TASK-D04 | 创建 Input 组件 | P0 | 4h | TASK-D01 | ✅ 已完成 |
| TASK-D05 | 重构 FileView | P1 | 8h | TASK-D02/D03 | ✅ 已完成 |
| TASK-D06 | 重构 TeamView | P1 | 6h | TASK-D02/D03 | ✅ 已完成 |
| TASK-D07 | 重构 SpaceView | P1 | 6h | TASK-D02/D03 | ✅ 已完成 |
| TASK-D08 | 重构 Admin Dashboard | P1 | 8h | TASK-D02/D03 | ✅ 已完成 |
| TASK-D09 | 重构剩余视图 | P2 | 8h | TASK-D02/D03 | ✅ 已完成 |
| TASK-D10 | 更新 App.vue | P2 | 4h | TASK-D01 | ✅ 已完成 |

**总工时**: 约 60h

---

## 四、任务详情

### TASK-D01: 创建 Design Tokens CSS

**优先级**: P0
**预估工时**: 4h
**依赖**: 无

**输出文件**: `web/src/assets/tokens.css`

**具体内容**:

```css
/* ===== COLORS ===== */
:root {
  /* Brand & Accent */
  --color-primary: #0066cc;
  --color-primary-focus: #0071e3;
  --color-primary-on-dark: #2997ff;

  /* Surface - Light */
  --color-canvas: #ffffff;
  --color-canvas-parchment: #f5f5f7;
  --color-surface-pearl: #fafafc;

  /* Surface - Dark */
  --color-surface-tile-1: #272729;
  --color-surface-tile-2: #2a2a2c;
  --color-surface-tile-3: #252527;
  --color-surface-black: #000000;

  /* Text */
  --color-ink: #1d1d1f;
  --color-body-on-dark: #ffffff;
  --color-body-muted: #cccccc;
  --color-ink-muted-80: #333333;
  --color-ink-muted-48: #7a7a7a;

  /* Borders */
  --color-divider-soft: #f0f0f0;
  --color-hairline: #e0e0e0;

  /* On Primary */
  --color-on-primary: #ffffff;
}

/* ===== TYPOGRAPHY ===== */
:root {
  --font-display: "SF Pro Display", system-ui, -apple-system, sans-serif;
  --font-body: "SF Pro Text", system-ui, -apple-system, sans-serif;

  /* Scale */
  --text-hero-display: 56px/1.07 -0.28px;
  --text-display-lg: 40px/1.1 0;
  --text-display-md: 34px/1.47 -0.374px;
  --text-lead: 28px/1.14 0.196px;
  --text-tagline: 21px/1.19 0.231px;
  --text-body-strong: 17px/1.24 -0.374px 600;
  --text-body: 17px/1.47 -0.374px;
  --text-caption: 14px/1.43 -0.224px;
  --text-button-utility: 14px/1.29 -0.224px;
  --text-nav-link: 12px/1.0 -0.12px;
}

/* ===== SPACING ===== */
:root {
  --space-xxs: 4px;
  --space-xs: 8px;
  --space-sm: 12px;
  --space-md: 17px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-xxl: 48px;
  --space-section: 80px;
}

/* ===== ROUNDED ===== */
:root {
  --rounded-none: 0px;
  --rounded-xs: 5px;
  --rounded-sm: 8px;
  --rounded-md: 11px;
  --rounded-lg: 18px;
  --rounded-pill: 9999px;
  --rounded-full: 9999px;
}

/* ===== COMPONENTS ===== */
/* Button Primary - 签名 Apple pill 按钮 */
.btn-primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
  font: var(--text-body);
  border-radius: var(--rounded-pill);
  padding: 11px 22px;
  border: none;
  cursor: pointer;
  transition: transform 0.1s;
}
.btn-primary:active { transform: scale(0.95); }
.btn-primary:focus { outline: 2px solid var(--color-primary-focus); }

/* Button Secondary - Ghost pill */
.btn-secondary {
  background: transparent;
  color: var(--color-primary);
  font: var(--text-body);
  border: 1px solid var(--color-primary);
  border-radius: var(--rounded-pill);
  padding: 11px 22px;
  cursor: pointer;
}
.btn-secondary:active { transform: scale(0.95); }

/* Button Dark Utility - 导航工具按钮 */
.btn-dark-utility {
  background: var(--color-ink);
  color: var(--color-body-on-dark);
  font: var(--text-button-utility);
  border-radius: var(--rounded-sm);
  padding: 8px 15px;
  border: none;
  cursor: pointer;
}
.btn-dark-utility:active { transform: scale(0.95); }

/* Search Input - Pill 搜索框 */
.search-input {
  background: var(--color-canvas);
  color: var(--color-ink);
  font: var(--text-body);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: var(--rounded-pill);
  padding: 12px 20px;
  height: 44px;
}

/* Store Utility Card - 18px 圆角卡片 */
.card-utility {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--rounded-lg);
  padding: var(--space-lg);
}

/* Product Tile - 全出血标题卡片 */
.tile-light {
  background: var(--color-canvas);
  padding: var(--space-section);
}
.tile-dark {
  background: var(--color-surface-tile-1);
  color: var(--color-body-on-dark);
  padding: var(--space-section);
}

/* Global Nav - 44px 黑色导航栏 */
.global-nav {
  background: var(--color-surface-black);
  color: var(--color-body-on-dark);
  font: var(--text-nav-link);
  height: 44px;
}
```

**验收标准**:
- [ ] tokens.css 包含所有 color token
- [ ] tokens.css 包含所有 typography token
- [ ] tokens.css 包含 spacing/rounded token
- [ ] 组件样式遵循 Apple spec

---

### TASK-D02: 构建 Button 组件

**优先级**: P0
**预估工时**: 6h
**依赖**: TASK-D01

**输出文件**:
- `web/src/components/common/ButtonPrimary.vue`
- `web/src/components/common/ButtonSecondary.vue`
- `web/src/components/common/ButtonDarkUtility.vue`
- `web/src/components/common/ButtonPearl.vue`
- `web/src/components/common/ButtonIcon.vue`

**ButtonPrimary.vue**:
```vue
<template>
  <button class="btn-apple-primary" :class="{ 'btn-icon-only': iconOnly }">
    <slot />
  </button>
</template>

<script setup>
defineProps({
  iconOnly: Boolean
})
</script>

<style scoped>
.btn-apple-primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
  font: var(--text-body);
  border-radius: var(--rounded-pill);
  padding: 11px 22px;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: transform 0.1s;
}
.btn-apple-primary:active { transform: scale(0.95); }
.btn-apple-primary:focus { outline: 2px solid var(--color-primary-focus); outline-offset: 2px; }
.btn-apple-primary.btn-icon-only { padding: 11px; width: 44px; height: 44px; justify-content: center; }
</style>
```

**验收标准**:
- [ ] 5 种按钮组件创建完成
- [ ] 支持默认/hover/active/focus 状态
- [ ] 支持 icon-only 模式 (44x44)
- [ ] active 状态 scale(0.95)

---

### TASK-D03: 构建 Card 组件

**优先级**: P0
**预估工时**: 6h
**依赖**: TASK-D01

**输出文件**:
- `web/src/components/common/CardBase.vue`
- `web/src/components/common/CardUtility.vue`
- `web/src/components/common/TileLight.vue`
- `web/src/components/common/TileDark.vue`

**CardUtility.vue** (Store Utility Card):
```vue
<template>
  <div class="card-utility">
    <slot />
  </div>
</template>

<style scoped>
.card-utility {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--rounded-lg);
  padding: var(--space-lg);
}
</style>
```

**验收标准**:
- [ ] 4 种卡片组件创建完成
- [ ] CardBase: 基础容器，1px hairline border
- [ ] CardUtility: 18px radius, 24px padding
- [ ] TileLight/TileDark: 全出血布局，80px section padding

---

### TASK-D04: 创建 Input 组件

**优先级**: P0
**预估工时**: 4h
**依赖**: TASK-D01

**输出文件**:
- `web/src/components/common/SearchInput.vue`
- `web/src/components/common/TextInput.vue`
- `web/src/components/common/FormField.vue`

**验收标准**:
- [ ] SearchInput: pill 形状, 44px height, 搜索图标
- [ ] TextInput: Apple 风格输入框
- [ ] FormField: label + input 组合

---

### TASK-D05: 重构 FileView

**优先级**: P1
**预估工时**: 8h
**依赖**: TASK-D02, TASK-D03

**改造要点**:
1. 文件列表使用 CardUtility 样式
2. 操作按钮使用 ButtonPrimary/Secondary
3. 应用 SF Pro Typography
4. 面包屑导航使用 Apple 风格
5. 响应式布局

**验收标准**:
- [ ] 文件列表 Apple 风格卡片
- [ ] 按钮使用 pill shape
- [ ] 间距统一使用 8px 单位
- [ ] 整体风格与 DESIGN.md 一致

---

### TASK-D06: 重构 TeamView

**优先级**: P1
**预估工时**: 6h
**依赖**: TASK-D02, TASK-D03

**改造要点**:
- 团队卡片使用 CardUtility
- 成员列表清晰分组
- pill 形状 CTAs

**验收标准**:
- [ ] 团队列表 Apple 卡片布局
- [ ] 创建/加入团队按钮 pill 样式
- [ ] 成员管理按钮一致风格

---

### TASK-D07: 重构 SpaceView

**优先级**: P1
**预估工时**: 6h
**依赖**: TASK-D02, TASK-D03

**改造要点**:
- 空间卡片使用 store-utility-card 风格
- 配额显示使用 Apple 数据展示

**验收标准**:
- [ ] 空间列表 CardUtility 布局
- [ ] 配额使用统一 typography
- [ ] 工作流/笔记本 tab 清晰

---

### TASK-D08: 重构 Admin Dashboard

**优先级**: P1
**预估工时**: 8h
**依赖**: TASK-D02, TASK-D03

**改造要点**:
- 使用 dark tile 风格 (#272729)
- ECharts 图表适配深色主题
- Apple 风格的数据展示
- 告警列表使用 tile-dark

**涉及文件**:
- `views/AdminDashboard.vue`
- `views/AdminTeams.vue`
- `views/admin/PoolConfig.vue`
- `views/admin/QuotaDashboard.vue`
- `views/admin/RoleConfig.vue`
- `components/admin/*`

**验收标准**:
- [ ] Admin 使用深色 tile 背景
- [ ] 图表配色 Apple 风格
- [ ] 告警使用 Action Blue 高亮

---

### TASK-D09: 重构剩余视图

**优先级**: P2
**预估工时**: 8h
**依赖**: TASK-D02, TASK-D03

**涉及文件**:
| 视图 | 改造要点 |
|------|---------|
| LoginView | 居中卡片，Apple 登录框 |
| StoragePoolView | CardUtility 布局 |
| KnowledgeView | 知识库卡片 |
| TrashView | 回收站列表 |
| Sidebar | global-nav 风格，44px 高，黑色背景 |
| FloatingWindow | 浮窗适配 |

**验收标准**:
- [ ] 所有视图 Apple 风格统一
- [ ] Sidebar 使用 global-nav 规范

---

### TASK-D10: 更新 App.vue

**优先级**: P2
**预估工时**: 4h
**依赖**: TASK-D01

**改造要点**:
- 导入 tokens.css
- 应用全局 CSS 变量
- 导航结构 Apple 风格
- 响应式断点

**验收标准**:
- [ ] tokens.css 全局导入
- [ ] 布局响应 Apple 断点
- [ ] 路由切换流畅

---

## 五、布局规范 (来自 DESIGN.md)

### 页面节奏
```
Light Hero → Dark Tile → Light Utility → Dark Tile → Parchment Footer
```

### Apple 断点
| 名称 | 宽度 | 关键变化 |
|------|------|---------|
| Small phone | ≤419px | 单列 |
| Phone | 420-640px | 单列，图片 80% |
| Large phone | 641-735px | padding 48px |
| Tablet portrait | 736-833px | hamburger 导航 |
| Tablet landscape | 834-1023px | 2 列 grid |
| Small desktop | 1024-1068px | 2/3 宽度 |
| Desktop | 1069-1440px | 满布局 |
| Wide desktop | ≥1441px | 1440px max |

### 间距系统
- 基础单位: 8px
- 常用: 4/8/12/17/24/32/48/80px
- Section padding: 80px

---

## 六、颜色规范 (来自 DESIGN.md)

### 品牌色
| Token | Hex | 用途 |
|-------|-----|------|
| primary | #0066cc | 所有交互元素 |
| primary-focus | #0071e3 | Focus 环 |
| primary-on-dark | #2997ff | 深色背景链接 |

### 表面色
| Token | Hex | 用途 |
|-------|-----|------|
| canvas | #ffffff | 主画布 |
| canvas-parchment | #f5f5f7 | 交替浅色块 |
| surface-pearl | #fafafc | 次要按钮 |
| surface-tile-1 | #272729 | 深色 tile |
| surface-tile-2 | #2a2a2c | 深色 tile 2 |
| surface-tile-3 | #252527 | 深色 tile 3 |
| surface-black | #000000 | 全黑导航 |

### 文字色
| Token | Hex | 用途 |
|-------|-----|------|
| ink | #1d1d1f | 深色文字 |
| body-on-dark | #ffffff | 浅色文字 |
| body-muted | #cccccc | 次要文字 |
| ink-muted-80 | #333333 | 按钮文字 |
| ink-muted-48 | #7a7a7a | 禁用文字 |

---

## 七、排版规范 (来自 DESIGN.md)

### 字体
- Display: SF Pro Display
- Body: SF Pro Text
- Fallback: system-ui, -apple-system, sans-serif

### 字号
| Token | Size | Weight | Line Height | Letter Spacing | 用途 |
|-------|------|--------|-------------|----------------|------|
| hero-display | 56px | 600 | 1.07 | -0.28px | Hero 标题 |
| display-lg | 40px | 600 | 1.10 | 0 | Tile 标题 |
| display-md | 34px | 600 | 1.47 | -0.374px | 章节标题 |
| lead | 28px | 400 | 1.14 | 0.196px | Tile 副标题 |
| tagline | 21px | 600 | 1.19 | 0.231px | 子导航 |
| body-strong | 17px | 600 | 1.24 | -0.374px | 强调正文 |
| body | 17px | 400 | 1.47 | -0.374px | 正文 |
| caption | 14px | 400 | 1.43 | -0.224px | 注释 |
| button-utility | 14px | 400 | 1.29 | -0.224px | 按钮 |
| nav-link | 12px | 400 | 1.0 | -0.12px | 导航 |

**注意**: 不要使用 weight 500/700，只用 300/400/600

---

## 八、圆角规范 (来自 DESIGN.md)

| Token | Value | 用途 |
|-------|-------|------|
| none | 0px | 全出血 tile |
| xs | 5px | 罕见 |
| sm | 8px | 工具按钮 |
| md | 11px | Pearl 按钮 |
| lg | 18px | 卡片 |
| pill | 9999px | 主 CTA/搜索 |
| full | 9999px | 圆形按钮 |

---

## 九、投影规范 (来自 DESIGN.md)

**唯一允许的投影** (仅用于产品图):
```css
box-shadow: rgba(0, 0, 0, 0.22) 3px 5px 30px 0;
```

**不要给**:
- 卡片加阴影
- 按钮加阴影
- 文字加阴影

---

## 十、任务分配建议

| 开发者 | 建议任务 |
|--------|---------|
| 前端负责人 A | TASK-D01 (Design Tokens) → TASK-D02 (Buttons) → TASK-D03 (Cards) |
| 前端负责人 B | TASK-D01 完成后并行 → TASK-D04 (Inputs) → TASK-D05 (FileView) |
| 前端成员 C | TASK-D06 (TeamView) → TASK-D07 (SpaceView) |
| 前端成员 D | TASK-D08 (Admin Dashboard) |
| 前端成员 E | TASK-D09 (剩余视图) → TASK-D10 (App.vue) |

---

## 十一、验收检查清单

每个任务完成后检查:

- [ ] 设计 Token 正确使用 (CSS 变量)
- [ ] 颜色符合 Apple 规范
- [ ] 字体使用 SF Pro / system-ui
- [ ] 字重使用 300/400/600 (无 500/700)
- [ ] 字间距符合规范
- [ ] 按钮使用 pill shape (rounded-pill)
- [ ] 按钮 active 状态 scale(0.95)
- [ ] 卡片使用 18px radius (rounded-lg)
- [ ] 间距使用 8px 基础单位
- [ ] 无多余阴影 (仅产品图可加阴影)
- [ ] 响应式布局正常

---

## 十二、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0 | 2026-05-05 | 初始版本，10 个改造任务 |
| **1.1** | **2026-05-05** | **D01/D02/D03 已完成**: tokens.css, 5个Button组件, 4个Card/Tile组件 |
| **1.2** | **2026-05-05** | **D09/D10 已完成**: LoginView, Sidebar, StoragePoolView, KnowledgeView, TrashView, FloatingWindow, App.vue 全部 Apple 风格化 |