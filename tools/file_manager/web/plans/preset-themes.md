# 预设主题功能实现计划

## Context

用户希望替换 Apple Design System 的蓝黑配色为"浅色清新 + 活力橙"风格，并添加一键换配色功能。项目已有完整的主题系统（ThemePanel + themeStore），但缺少预设主题快速切换功能。

## 实现方案

### 1. 在 themeStore.js 中添加预设主题

**文件**: `/Users/xzmx/Downloads/my-project/hermes-agent/tools/file_manager/web/src/stores/themeStore.js`

添加预设主题定义和切换方法：

```javascript
// 预设主题定义
const PRESET_THEMES = {
  'apple-blue': { name: 'Apple 蓝', primary: '#0066cc', ... },
  'warm-orange': { name: '活力橙', primary: '#f97316', ... },
  'fresh-green': { name: '清新绿', primary: '#10b981', ... },
  'purple': { name: '薰衣草紫', primary: '#8b5cf6', ... },
  'neutral-gray': { name: '中性灰', primary: '#6b7280', ... }
}

// 新增方法
function applyPresetTheme(themeId) { ... }
function getPresetThemes() { return PRESET_THEMES }
```

### 2. 修改 ThemePanel.vue 添加预设主题选择 UI

**文件**: `/Users/xzmx/Downloads/my-project/hermes-agent/tools/file_manager/web/src/components/common/ThemePanel.vue`

在现有 UI 基础上添加：
- 预设主题卡片网格（顶部）
- 当前主题高亮指示
- 一键应用按钮

### 3. 更新 Sidebar 配色按钮交互

确保 ThemePanel 可通过 Sidebar 触发。

## 关键文件

- `src/stores/themeStore.js` - 主题状态管理
- `src/components/common/ThemePanel.vue` - 主题配置面板
- `src/components/common/ColorPicker.vue` - 颜色选择器

## 验证

1. 启动开发服务器 `npm run dev`
2. 打开 http://localhost:5173/vue.html
3. 点击 Sidebar 底部"配色调整"按钮
4. 验证预设主题显示正确
5. 点击各预设主题，验证颜色切换生效
6. 刷新页面，验证主题偏好持久化
