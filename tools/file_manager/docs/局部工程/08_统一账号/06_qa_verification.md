# 同事讨论内容准确性审核

> **审核日期**: 2026-05-13
> **状态**: ✅ 已核实
> **说明**: 以下内容已与用户确认

---

## 一、事实性内容（已核实）

| 序号 | 内容 | 来源说明 | 准确性评估 | 备注 |
|------|------|----------|-------------|------|
| 1 | Claudian 是 MIT 开源协议 | 用户确认 | ✅ **确认正确** | |
| 2 | Claudian 作者是 YishenTu | 用户确认 | ✅ **确认正确** | GitHub: YishenTu/claudian |
| 3 | Obsidian 是闭源软件，Freemium 模式 | 用户确认 | ✅ **确认正确** | |
| 4 | llm_wiki 基于 Tauri v2 + React | 代码核实 | ✅ **确认正确** | 不是 Vue，是 React + TypeScript |
| 5 | llm_wiki 开源协议 GPL | 用户确认 | ✅ **确认正确** | |
| 6 | llm_wiki GitHub | 用户提供 | ✅ **确认正确** | nashsu/llm_wiki |
| 7 | Claudian GitHub | 用户提供 | ✅ **确认正确** | YishenTu/claudian |
| 8 | Claude Code 是闭源商业产品 | 用户确认 | ✅ **确认正确** | |
| 9 | Claude Code 源码泄露事件 (2026-03-31) | 用户确认 | ✅ **确认有此事** | 非正式开源，闭源产品 |

---

## 二、观点性内容（合理性评估）

| 序号 | 内容 | 评估 | 备注 |
|------|------|------|------|
| 1 | Claudian 本身 ≠ LLM Wiki，需要手动引导 | ✅ 合理 | 符合工具定位 |
| 2 | 判断标准：CLAUDE.md + 三层目录 + Ingest 流程 + log.md | ✅ 合理 | 可操作性强 |
| 3 | llm_wiki vs Claudian 是"二选一"关系 | ⚠️ 部分正确 | 实际可互补使用 |
| 4 | 读写分离架构是最佳协作方案 | ✅ 合理 | 避免文件冲突 |
| 5 | Git 同步是可行的多用户方案 | ✅ 合理 | 利用现有生态 |
| 6 | llm_wiki 内置完整 LLM Wiki 工作流 | ✅ 合理 | 开箱即用 |
| 7 | Claudian 需要手动配置才能运行 LLM Wiki | ✅ 合理 | 插件本质 |

---

## 三、存疑内容清单

### 3.1 已解决

| 项目 | 原存疑 | 结论 |
|------|--------|------|
| llm_wiki 技术栈 | 同事描述 Vue | ✅ 核实为 **React + TypeScript** |
| llm_wiki Stars 数量 | 3600+ | 无需核实，已提供 GitHub 链接 |
| Claudian Stars 数量 | 4500+ | 无需核实，已提供 GitHub 链接 |
| Claude Code 泄露事件 | 无法核实 | ✅ 用户确认确有此事 |

### 3.2 开源信息汇总

| 工具 | GitHub | 协议 |
|------|--------|------|
| Claudian | https://github.com/YishenTu/claudian | MIT |
| llm_wiki | https://github.com/nashsu/llm_wiki | GPL |

### 3.3 技术栈核实

| 工具 | 实际技术栈 |
|------|-----------|
| llm_wiki | Tauri v2 + React + TypeScript + Vite + Tailwind CSS |

---

## 四、文档更新状态

| 原文档 | 更新内容 | 状态 |
|--------|---------|------|
| 04_claudian_guide.md | ✅ 已补充 Claude Code 与 Claudian 的本质区别 | 已完成 |
| 04_claudian_guide.md | ✅ 已补充 Claude Code 泄露事件说明 | 已完成 |
| 05_llmwiki_detail.md | ✅ 已补充 llm_wiki 开源情况和 GitHub 链接 | 已完成 |
| 05_llmwiki_detail.md | ✅ 已修正技术栈为 React (非 Vue) | 已完成 |

---

## 五、一句话总结

- **llm_wiki**: 开源 GPL，基于 Tauri v2 + React + TypeScript，GitHub: nashsu/llm_wiki
- **Claudian**: 开源 MIT，基于 Claude Code CLI，GitHub: YishenTu/claudian
- **Claude Code**: 闭源产品，2026-03-31 确有源码泄露事件
- **Obsidian**: 闭源 Freemium
4. **Claude Code 泄露事件**: 你是否有相关信息？

---

## 六、文档更新建议

| 文档 | 建议更新内容 |
|------|-------------|
| `04_claudian_guide.md` | 补充"Claudian vs Claude Code 本质区别"章节 |
| `01_obsidian_vs_llmwiki.md` | 确认后补充工具对比表格 |
| `05_llmwiki_detail.md` | 补充 llm_wiki 开源协议和 Stars 信息 |

是否确认以上内容？确认后我将：
1. 更新相关文档
2. 补充 Claude Code 与 Claudian 的本质区别说明
3. 更新工具对比内容
