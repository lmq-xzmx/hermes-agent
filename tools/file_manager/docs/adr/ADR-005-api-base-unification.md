# ADR-005: API_BASE 统一

## 状态
✅ 已接受

## 日期
2026-05-05

## 背景
Web 和 Tauri 环境使用不同的 API 地址，导致环境差异问题。

## 决策
统一使用 `http://localhost:8080/api/v1`：
- 前端代码无环境判断
- Web 开发环境和 Tauri 生产环境使用相同 API 地址
- 通过构建时注入配置

## 理由
1. **一致性**：代码无环境分支，更易于理解
2. **简化调试**：开发时验证的代码直接用于生产
3. **符合 SSOT**：单一构建产物，多环境共用

## 实现方式
```javascript
// vite.config.js
define: {
    __API_BASE__: JSON.stringify('http://localhost:8080/api/v1')
}

// 前端代码
const API_BASE = __API_BASE__;
```

## 后果
- ✅ 环境一致性
- ✅ 代码简化
- ⚠️ API 地址硬编码（可接受，本地为开发环境）

## 相关文档
- `GOALS.md` G5 - API 统一目标
- `README_BUILD.md` - 构建配置
