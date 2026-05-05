# ADR-004: LLM Wiki 迁移 Web 层

## 状态
📋 规划中（Rust 仍有 open_llm_wiki 实现）

## 日期
2026-05-05

## 背景
LLM Wiki 功能目前仍在 Rust 层实现，需要迁移到 Web 层以符合 Tauri 壳最低维护原则。

## 决策
将 LLM Wiki 功能迁移到 Web 层：
- 删除 Rust 中的 `spawn_llm_wiki_gui()` 函数
- 删除 Rust 中的 `get_llm_wiki_bundle()` 函数
- 删除 Rust 中的 `get_llm_wiki_status()` command
- 删除 Rust 中的 `open_llm_wiki()` command
- Web 层通过 API 调用实现相同功能

## 理由
1. **最低维护**：Rust 代码行数需 ≤ 200 行
2. **职责分离**：Tauri 壳不承载业务逻辑
3. **技术匹配**：Web 层更适合 UI 交互

## 预期效果
- Rust 代码精简约 50 行
- LLM Wiki 功能通过 Python API 提供

## 后果
- ✅ Rust 代码减少
- ✅ 架构更清晰
- ⚠️ 需要 API 层支持

## 相关文档
- `GOALS.md` G1 - Tauri 最低维护目标
- `TASK-001` - Rust 精简任务
