# ADR-001: Web 优先架构

## 状态
✅ 已达成

## 日期
2026-05-05

## 背景
Hermes File Manager 需要在多端（桌面、移动、Web）提供一致的用户体验，同时保持较低的维护成本。

## 决策
采用 "Web 优先 + Tauri 壳" 模式：
- Web 是产品，Tauri 仅作为桌面交付渠道
- 产品功能、UI/UE、交互逻辑在 Web 端开发和测试
- Tauri 仅负责桌面窗口包装，不承载业务逻辑

## 理由
1. **维护成本**：Tauri Rust 代码 ≤ 200 行，最低维护量
2. **开发效率**：Web 开发工具链成熟，热重载、调试友好
3. **代码复用**：一套代码支持多端（Web + Tauri）
4. **行业验证**：Figma 等产品采用类似架构

## 后果
- ✅ 维护成本低
- ✅ 开发效率高
- ✅ 架构清晰
- ✅ Vue 3 SPA 已完成（Phase 1-3 全部完成）
- ✅ vue.html 作为主入口
- ✅ Tauri 集成已配置 (tauri.conf.json 指向 vue.html)
- ⚠️ 需要处理 Web 和 Tauri 环境差异（通过 PlatformAdapter 解决）

## 相关文档
- `GOALS.md` - 目标体系
- `domain:Tauri&web.md` - 领域知识
