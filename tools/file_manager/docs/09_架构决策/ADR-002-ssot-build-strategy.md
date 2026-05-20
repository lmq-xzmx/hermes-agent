# ADR-002: SSOT 构建策略

## 状态
✅ 已接受

## 日期
2026-05-05

## 背景
需要确保 Web 和 Tauri 使用相同的构建产物，避免界面不一致。

## 决策
采用 SSOT (Single Source of Truth) 策略：
- `web/dist/` 是唯一前端构建产物
- 前端只构建一次，同时用于 Web 和 Tauri
- Tauri 直接嵌入 `web/dist/` 作为静态资源

## 理由
1. **一致性**：Web 和 Tauri 使用完全相同的代码
2. **简化流程**：单一构建源，无需维护多套产物
3. **调试方便**：开发时验证的产物直接用于生产

## 实现方式
```json
// tauri.conf.json
{
  "bundle": {
    "resources": ["../web/dist"]
  }
}
```

## 后果
- ✅ 界面完全一致
- ✅ 构建流程简化
- ❌ Web 更新需要重新打包 Tauri（嵌入模式）
- ❌ 独立部署需要额外配置 CORS

## 相关文档
- `GOALS.md` G3 - SSOT 目标
- `README_BUILD.md` - 构建流程
