# ADR-007: _up_ URL workaround

## 状态
🔄 已废弃（G8 已达成，迁移到标准路径）

## 日期
2026-05-05

## 背景
Tauri 2.x glob bug 导致无法使用标准路径 `app.html`，需要使用 `_up_/web/dist/app.html` workaround。

## 决策
接受 `_up_/web/dist/app.html` 作为当前标准路径：
- 不等待 Tauri 修复
- 不采用手动复制方案
- 将 workaround 作为当前标准

## 配置
```json
// tauri.conf.json (历史配置，已废弃)
{
  "app": {
    "windows": [{
      "url": "_up_/web/dist/app.html"  // ❌ 已废弃
    }]
  }
}

// 当前标准配置 (G8 已达成)
{
  "app": {
    "windows": [{
      "url": "vue.html"  // ✅ 标准路径
    }]
  }
}
```

## 理由
1. **功能正常**：`_up_` 路径可以正常工作
2. **无等待成本**：不等 Tauri 修复
3. **无复杂性**：无需手动复制脚本
4. **可回归**：Tauri 修复后可回归标准路径

## 替代方案分析

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| A. 等待 Tauri 修复 | 无需改动 | 时间不确定 | ❌ 不采用 |
| B. 接受现状 | 立即可用 | 非标准路径 | ❌ 已废弃（G8 达成） |
| C. 手动复制 | 可控 | 增加复杂性 | ❌ 不采用 |
| **D. 标准路径** | **符合规范** | **需要 Tauri 修复** | **✅ G8 已达成** |

## 实施状态
G8 已达成：vue.html 作为标准入口路径，不再使用 `_up_/web/dist/app.html` workaround。

## 后果
- ✅ G8 已达成：vue.html 作为标准入口路径
- ✅ 不再使用 `_up_/web/dist/app.html` workaround
- ✅ 路径符合 Tauri 2.x 标准

## 相关文档
- `GOALS.md` G8 - 窗口 URL 标准化目标
- `domain:Tauri&web.md` - HIST-017 问题记录
