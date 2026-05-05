# Apple Design System 前端全面改造设计

> **版本**: v1.0
> **日期**: 2026-05-05
> **状态**: 已批准
> **项目**: Hermes File Manager 前端改造

---

## 1. 背景与目标

### 1.1 背景

根据 `DESIGN.md` (Apple Design System) 规范，项目前端需要全面改造以符合 Apple 设计语言。当前状态：
- `tokens.css` 已完成 ✅
- 部分组件已完成改造
- 大量组件存在 CSS 变量使用不规范、硬编码 fallback 等问题

### 1.2 目标

将所有前端组件改造为符合 Apple Design System 规范，确保：
- 视觉一致性
- 代码可维护性
- 长期设计系统统一

---

## 2. 改造策略

### 2.1 策略选择

| 维度 | 选择 |
|------|------|
| 改造策略 | 增量式，每次1个组件 |
| 优先级 | 高频基础组件 → 业务页面 → 问题组件 |
| 验收标准 | 功能不变 → 视觉一致 → 两者兼顾 |
| 验证方式 | 测试 + 手动验证 |

### 2.2 策略说明

**增量式改造**：每次只改造1个组件，完全验证通过后再进行下一个
- 优点：风险低、可测试、容易回滚
- 适用场景：58个组件量大、改造状态不一

**优先级 B+A**：高频基础组件优先
- Phase 1: 高频基础组件（common/）
- Phase 2: 业务页面（views/）
- Phase 3: 问题组件

**验收标准递进**：A → B → C
- 基础组件：功能不变
- 业务页面：视觉一致
- 问题组件：两者兼顾

---

## 3. 组件优先级

### Phase 1: 高频基础组件（功能不变）

| 序号 | 组件 | 路径 | 问题类型 |
|------|------|------|---------|
| 1 | TextInput | components/common/ | 间距硬编码 |
| 2 | Dropdown | components/common/ | 缺少字体变量 |
| 3 | Modal | components/common/ | 阴影误用 |
| 4 | SearchInput | components/common/ | 待检查 |
| 5 | Tabs | components/common/ | 待检查 |
| 6 | Toast | components/common/ | 待检查 |

### Phase 2: 业务页面（视觉一致）

| 序号 | 组件 | 路径 | 问题类型 |
|------|------|------|---------|
| 7 | LoginView | views/ | 大量 fallback |
| 8 | FileView | views/ | 大量 fallback |
| 9 | Sidebar | views/ | 待检查 |

### Phase 3: 问题组件（两者兼顾）

| 序号 | 组件 | 路径 | 问题类型 |
|------|------|------|---------|
| 10 | FileContextMenu | components/ | 字体变量错误 |
| 11 | DebugPanel | components/ | 字体变量错误 |

### 后续组件

根据前三阶段经验继续改造剩余组件：
- components/admin/ 下所有组件
- components/approval/ 下所有组件
- components/lifecycle/ 下所有组件
- views/ 下其他组件

---

## 4. 改造检查清单

每个组件改造必须满足以下检查项：

### 4.1 CSS 变量规范

| 检查项 | 规范 | 错误示例 | 正确示例 |
|--------|------|---------|---------|
| 颜色 | 使用 `var(--color-*)` | `#0066cc`, `red` | `var(--color-primary)` |
| 字体 | 使用 `var(--font-family-*)` | `var(--font-body)` | `var(--font-family-text)` |
| 间距 | 使用 `var(--spacing-*)` | `padding: 11px 15px` | `padding: var(--spacing-sm)` |
| 圆角 | 使用 `var(--radius-*)` | `border-radius: 8px` | `border-radius: var(--radius-sm)` |

### 4.2 Apple Design 特殊规范

| 检查项 | 规范 |
|--------|------|
| 阴影 | 仅产品图使用 `var(--shadow-product)`，禁止用于卡片/按钮/文字 |
| 按钮 active 状态 | 使用 `transform: scale(0.95)` |
| fallback 模式 | 禁止 `var(--xxx, #hardcode)` 模式 |

### 4.3 变量映射表

**字体变量**（必须使用）：

| 旧变量 | 新变量 |
|--------|--------|
| `var(--font-body)` | `var(--font-family-text)` |
| `var(--font-display)` | `var(--font-family-display)` |
| `var(--text-body)` | `var(--font-family-text)` |
| `var(--text-*)` (text-* 系列) | 对应 `var(--font-family-*)` |

**间距变量**（必须使用）：

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

**圆角变量**（必须使用）：

| 值 | 变量 | 用途 |
|----|------|------|
| 0px | `var(--radius-none)` | 全出血 tile |
| 5px | `var(--radius-xs)` | 内联链接 chip |
| 8px | `var(--radius-sm)` | 工具按钮 |
| 11px | `var(--radius-md)` | Pearl Button |
| 18px | `var(--radius-lg)` | 卡片 |
| 9999px | `var(--radius-pill)` | 胶囊按钮、CTA |
| 9999px | `var(--radius-full)` | 圆形按钮 |

---

## 5. 验收流程

### 5.1 验证方式

| 组件类型 | 验证方式 |
|---------|---------|
| 基础组件（common/） | 自动化测试 + 手动验证 |
| 业务组件（views/） | 手动浏览器验证 |
| 问题组件 | 自动化测试 + 手动验证 + 差异记录 |

### 5.2 验收检查项

1. **功能验证**：组件交互行为与改造前一致
2. **视觉验证**：颜色、字体、间距、圆角符合规范
3. **代码审查**：无硬编码、无错误变量引用
4. **控制台检查**：无 CSS 变量未定义警告

### 5.3 差异记录

如果发现功能或视觉差异，记录到组件改造日志：

```markdown
## [组件名] 改造记录

**日期**: YYYY-MM-DD
**改造前问题**: ...
**改造后状态**: ...
**差异说明**: ...
**决定**: [接受/回滚/调整]
```

---

## 6. 实施计划

### Phase 1: 高频基础组件（6个）
预计工时：约 2-3 小时

### Phase 2: 业务页面（3个）
预计工时：约 2-3 小时

### Phase 3: 问题组件（2个）
预计工时：约 1-2 小时

### 后续组件
根据前三阶段经验和用户反馈继续推进

---

## 7. 相关文档

- `/Users/xzmx/Downloads/my-project/hermes-agent/DESIGN.md` - Apple Design System 规范
- `/Users/xzmx/Downloads/my-project/hermes-agent/tools/file_manager/docs/1_architecture/TOP_DOWN_DEVELOPMENT.md` - 自顶向下开发方法论
- `/Users/xzmx/Downloads/my-project/hermes-agent/tools/file_manager/web/src/assets/tokens.css` - 设计令牌定义

---

## 8. 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2026-05-05 | v1.0 | 初始版本 |
