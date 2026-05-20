# Apple Design System 重构任务清单

> **版本**: v1.0
> **更新日期**: 2026-05-05
> **参考规范**: DESIGN.md (Apple Design System)
> **目标**: 将当前 GitHub Dark Theme 重构为 Apple Design System
> **总工作量**: ~33h
> **设计系统**: Apple Design System - SF Pro Display/Text, Action Blue #0066cc, Pill Buttons

---

## 一、项目现状

### 1.1 当前设计系统
- **主题**: GitHub Dark Theme (非 Apple)
- **颜色**: `#0d1117` (bg), `#30363d` (border), `#58a6ff` (accent)
- **按钮圆角**: `6px` (应为 `9999px` pill)
- **阴影**: 过度使用 (Apple 规范仅产品图片有 shadow)
- **字体**: 无 SF Pro 字体族

### 1.2 Apple Design System 目标
- **主色**: `#0066cc` (Action Blue)
- **字体**: SF Pro Display / SF Pro Text
- **按钮**: Pill shape (`border-radius: 9999px`)
- **卡片圆角**: `18px` (`rounded-lg`)
- **阴影**: 仅产品图片使用唯一 shadow

---

## 二、CSS 变量/设计令牌缺失

### T1: 创建 Apple Design Token CSS 文件

| 属性 | 内容 |
|------|------|
| **任务代号** | T1 |
| **文件** | `src/assets/tokens.css` |
| **优先级** | P0 |
| **工作量** | 2h |
| **状态** | ✅ **已完成** |
| **依赖** | 无 |
| **完成日期** | 2026-05-05 |

**已完成内容**:
1. 创建 `src/assets/tokens.css` - Apple Design Token 定义文件
2. 更新 `vue.html` - 引入 tokens.css 并添加全局 Apple 基础样式
3. 定义所有 CSS 变量: 颜色、字体、间距、圆角、阴影
4. 提供组件样式类: `.btn-primary`, `.btn-secondary`, `.btn-dark`, `.search-input`, `.card`
5. 定义 Apple 规范: pill button、44px 触摸目标、scale(0.95) active 状态

**Token 变量定义**:
```css
:root {
  /* Brand & Accent */
  --color-primary: #0066cc;
  --color-primary-focus: #0071e3;
  --color-primary-on-dark: #2997ff;
  
  /* Surface */
  --color-canvas: #ffffff;
  --color-canvas-parchment: #f5f5f7;
  --color-surface-pearl: #fafafc;
  --color-surface-tile-1: #272729;
  --color-surface-tile-2: #2a2a2c;
  --color-surface-tile-3: #252527;
  --color-surface-black: #000000;
  
  /* Text */
  --color-ink: #1d1d1f;
  --color-body: #1d1d1f;
  --color-body-on-dark: #ffffff;
  --color-body-muted: #cccccc;
  --color-ink-muted-80: #333333;
  --color-ink-muted-48: #7a7a7a;
  
  /* Borders */
  --color-hairline: #e0e0e0;
  --color-divider-soft: #f0f0f0;
  
  /* Typography */
  --font-family-display: "SF Pro Display", system-ui, -apple-system, sans-serif;
  --font-family-text: "SF Pro Text", system-ui, -apple-system, sans-serif;
  
  /* Spacing (8px grid) */
  --spacing-xxs: 4px;
  --spacing-xs: 8px;
  --spacing-sm: 12px;
  --spacing-md: 17px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-xxl: 48px;
  --spacing-section: 80px;
  
  /* Border Radius */
  --radius-none: 0px;
  --radius-xs: 5px;
  --radius-sm: 8px;
  --radius-md: 11px;
  --radius-lg: 18px;
  --radius-pill: 9999px;
  --radius-full: 9999px;
  
  /* Shadows - Apple 唯一 shadow */
  --shadow-product: rgba(0, 0, 0, 0.22) 3px 5px 30px 0;
}
```

---

## 三、Typography 统一

### T2: 统一 Typography 体系

| 属性 | 内容 |
|------|------|
| **任务代号** | T2 |
| **文件** | 全局 CSS / 各视图 |
| **优先级** | P0 |
| **工作量** | 6h |
| **状态** | 📋 待处理 |
| **依赖** | T1 |

**修改项**:
1. 全局设置 `font-family: var(--font-family-text)`
2. Body text: `font-size: 17px; letter-spacing: -0.374px; line-height: 1.47`
3. 标题添加负 letter-spacing: `-0.374px` 到 `-0.28px`
4. 移除 weight 500 (Apple 使用 300/400/600/700)

**Apple Typography Token**:
| Token | Size | Weight | Line Height | Letter Spacing |
|-------|------|--------|-------------|----------------|
| body | 17px | 400 | 1.47 | -0.374px |
| body-strong | 17px | 600 | 1.24 | -0.374px |
| caption | 14px | 400 | 1.43 | -0.224px |
| button-utility | 14px | 400 | 1.29 | -0.224px |
| display-lg | 40px | 600 | 1.10 | 0 |
| hero-display | 56px | 600 | 1.07 | -0.28px |

---

## 四、按钮重构

### T3: 重构 Button 为 Apple Pill Shape

| 属性 | 内容 |
|------|------|
| **任务代号** | T3 |
| **文件** | 所有视图中的 .btn 类 |
| **优先级** | P0 |
| **工作量** | 4h |
| **状态** | 🔄 **进行中** |
| **依赖** | T1 |
| **完成日期** | 2026-05-05 |

**当前问题**:
```css
/* Before - 错误 */
.btn {
  border-radius: 6px;
  padding: 10px 16px;
  font-size: 14px;
}
```

**Apple 规范**:
```css
/* After - 正确 */
.btn {
  border-radius: var(--radius-pill); /* 9999px */
  padding: 11px 22px;
  font-size: 17px;
  font-family: var(--font-family-text);
  letter-spacing: -0.374px;
}

.btn:active {
  transform: scale(0.95);  /* Apple active state */
}
```

**受影响文件**:
- FileView.vue, FloatingWindow.vue, KnowledgeView.vue
- LoginView.vue, SpaceView.vue, StoragePoolView.vue
- TeamView.vue, TrashView.vue, AdminDashboard.vue, AdminTeams.vue

---

## 五、阴影移除

### T4: 移除不必要的 Shadows

| 属性 | 内容 |
|------|------|
| **任务代号** | T4 |
| **文件** | PreviewModal.vue, FileContextMenu.vue, DebugPanel.vue, ShortcutHints.vue, TourGuide.vue |
| **优先级** | P1 |
| **工作量** | 3h |
| **状态** | 📋 待处理 |
| **依赖** | T1 |

**Apple 规范**:
> Apple uses exactly ONE drop-shadow, and it is applied to photographic product imagery — never to cards, never to buttons, never to text.

**当前问题**:
```css
/* PreviewModal.vue - 过度使用 shadow */
box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4);

/* FileContextMenu.vue */
box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
```

**修改方案**:
```css
/* 改用 surface color 和 border 区分 */
border: 1px solid var(--color-hairline);
```

---

## 六、Card/Modal 圆角

### T5: 重构 Card/Modal Border Radius

| 属性 | 内容 |
|------|------|
| **任务代号** | T5 |
| **文件** | SpaceView.vue, StoragePoolView.vue, AdminTeams.vue, AdminDashboard.vue |
| **优先级** | P1 |
| **工作量** | 2h |
| **状态** | 📋 待处理 |
| **依赖** | T1 |

**修改**:
```css
/* Before */
border-radius: 8px;

/* After */
border-radius: var(--radius-lg); /* 18px */
```

---

## 七、Search Input 重构

### T6: 重构 Search Input 为 Pill Shape

| 属性 | 内容 |
|------|------|
| **任务代号** | T6 |
| **文件** | FileView.vue, FloatingWindow.vue, KnowledgeView.vue |
| **优先级** | P1 |
| **工作量** | 1h |
| **状态** | 📋 待处理 |
| **依赖** | T1 |

**当前问题**:
```css
.search-input {
  border-radius: 6px;  /* 应为 pill */
  padding: 6px 12px;  /* 应为 12px 20px */
  font-size: 13px;    /* 应为 17px */
  height: auto;       /* 应为 44px */
}
```

**Apple 规范**:
```css
.search-input {
  border-radius: var(--radius-pill); /* 9999px */
  padding: 12px 20px;
  height: 44px;
  font-size: 17px;
}
```

---

## 八、组件合并

### T7: 合并 ContextMenu.vue 和 FileContextMenu.vue

| 属性 | 内容 |
|------|------|
| **任务代号** | T7 |
| **文件** | src/components/ContextMenu.vue, src/components/FileContextMenu.vue |
| **优先级** | P2 |
| **工作量** | 2h |
| **状态** | 📋 待处理 |
| **依赖** | 无 |
| **可并行** | ✅ 与其他任务并行 |

**分析**:
- `ContextMenu.vue`: 通用右键菜单，支持自定义 items
- `FileContextMenu.vue`: 硬编码文件操作，可通过 props 配置

**合并方案**: FileContextMenu.vue 改为使用 ContextMenu 组件，通过 props 传入 file-specific items

---

### T8: 合并 TourGuide.vue 和 NotebookTourGuide.vue

| 属性 | 内容 |
|------|------|
| **任务代号** | T8 |
| **文件** | src/components/TourGuide.vue, src/components/NotebookTourGuide.vue |
| **优先级** | P2 |
| **工作量** | 1h |
| **状态** | 📋 待处理 |
| **依赖** | 无 |
| **可并行** | ✅ 与其他任务并行 |

**合并方案**: NotebookTourGuide.vue 简化为配置文件，使用 TourGuide.vue 的 slot 或 props

---

## 九、间距系统

### T9: 实现 8px 网格间距系统

| 属性 | 内容 |
|------|------|
| **任务代号** | T9 |
| **文件** | 全局 CSS / 各组件 |
| **优先级** | P2 |
| **工作量** | 4h |
| **状态** | 📋 待处理 |
| **依赖** | T1 |

**修改**: 将所有 padding/margin 调整为 8px 倍数

---

## 十、Light Mode

### T10: 添加 Light Mode 支持

| 属性 | 内容 |
|------|------|
| **任务代号** | T10 |
| **文件** | 全局 CSS |
| **优先级** | P2 |
| **工作量** | 8h |
| **状态** | 📋 待处理 |
| **依赖** | T1, T2, T3, T4, T5, T6 |

**Apple Design**: 亮暗交替的 tile 表面

**修改**: 添加 `@media (prefers-color-scheme: light)` 支持

---

## 十一、工作量汇总

| 优先级 | 任务 | 工作量 | 依赖 |
|--------|------|--------|------|
| **P0** | T1: 创建 Design Token | 2h | 无 |
| **P0** | T2: Typography 统一 | 6h | T1 |
| **P0** | T3: Button Pill Shape | 4h | T1 |
| **P1** | T4: 移除不必要 Shadows | 3h | T1 |
| **P1** | T5: Card Border Radius | 2h | T1 |
| **P1** | T6: Search Input Pill | 1h | T1 |
| **P2** | T7: ContextMenu 合并 | 2h | 无 |
| **P2** | T8: TourGuide 合并 | 1h | 无 |
| **P2** | T9: 8px 网格间距 | 4h | T1 |
| **P2** | T10: Light Mode | 8h | T1-T6 |
| **总计** | | **33h** | |

---

## 十二、受影响文件清单

### Views (11 个)
| 文件 | 大小 | 主要问题 |
|------|------|----------|
| FileView.vue | 28906 B | Button radius, Typography, shadow |
| FloatingWindow.vue | 9397 B | Button radius, Input radius |
| KnowledgeView.vue | 8233 B | Input radius, Button radius |
| LoginView.vue | 8846 B | Button radius, Input radius |
| Sidebar.vue | 3129 B | Nav styling, Button radius |
| SpaceView.vue | 31016 B | Card radius, Button radius, shadow |
| StoragePoolView.vue | 15372 B | Card radius, Button radius |
| TeamView.vue | 14204 B | Card radius, Button radius |
| TrashView.vue | 7132 B | Card radius, Button radius |
| AdminDashboard.vue | 3699 B | Card radius, grid layout |
| AdminTeams.vue | 4802 B | Card radius, table styling |

### Components (8 个)
| 文件 | 主要问题 |
|------|----------|
| ContextMenu.vue | shadow, radius |
| FileContextMenu.vue | 可合并 (T7) |
| DebugPanel.vue | shadow |
| PreviewModal.vue | shadow, radius |
| ShortcutHints.vue | shadow |
| TourGuide.vue | shadow |
| NotebookTourGuide.vue | 可合并 (T8) |

---

## 十三、推荐实施顺序

```
Phase 1 - Foundation
├── T1: 创建 Design Token (2h)
└── T2: Typography 统一 (6h)

Phase 2 - Buttons & Inputs
├── T3: Button Pill Shape (4h) ← 并行 → T6: Search Input Pill (1h)

Phase 3 - Cards & Shadows
├── T4: 移除不必要 Shadows (3h)
└── T5: Card Border Radius (2h)

Phase 4 - Components
├── T7: ContextMenu 合并 (2h) ← 并行 → T8: TourGuide 合并 (1h)
└── T9: 8px 网格间距 (4h)

Phase 5 - Light Mode
└── T10: Light Mode (8h) ← 依赖所有其他任务
```

---

## 十四、验收检查清单

### 代码质量
- [ ] 所有组件使用 Design Token CSS 变量
- [ ] 无硬编码颜色值 (应使用 `{colors.*}` 变量)
- [ ] Button 全部使用 pill shape (`border-radius: 9999px`)
- [ ] Card 全部使用 `border-radius: 18px`

### Typography
- [ ] 全局字体设置为 SF Pro Text
- [ ] Body text 为 17px / 400 / 1.47 / -0.374px
- [ ] 标题使用负 letter-spacing

### 阴影
- [ ] 组件无 shadow (除产品图片外)
- [ ] 使用 surface color 和 border 区分层级

### 间距
- [ ] 基于 8px 网格系统
- [ ] 无随机间距值 (20px, 16px, 12px 混用)

---

## 十五、变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| **v1.0** | **2026-05-05** | **初始版本**: Apple Design System 重构任务清单 |