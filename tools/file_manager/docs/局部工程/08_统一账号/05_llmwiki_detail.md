# LLM Wiki 详解

> **创建日期**: 2026-05-13
> **状态**: 已完成
> **来源**: LLM Wiki 官方 README 整理

---

## 一、概述

### 1.1 什么是 LLM Wiki？

LLM Wiki 是一款基于 **Karpathy's LLM Wiki 模式** 构建的跨平台桌面应用。核心理念：传统 RAG 每次查询从零检索，LLM Wiki 则让 LLM **增量构建并持久维护一个持久的 wiki**——知识被编译一次并保持最新，不需要每次查询时重新派生。

**一句话定义**: 一个会自动构建和完善自身的个人知识库。

### 1.2 核心区别：RAG vs 编译

| 对比项 | 传统 RAG | LLM Wiki |
|--------|----------|----------|
| **知识积累** | 每次从零检索，无积累 | 增量编译，具有复利效应 |
| **交叉引用** | 用户手动建立 | AI 自动维护 |
| **矛盾处理** | 用户自己发现 | AI 主动标注 |
| **查询效率** | 每次重新检索 | 基于已编译 wiki 快速回答 |
| **知识质量** | 依赖每次检索质量 | 越用越丰富、越精准 |

---

## 二、核心架构

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Raw Sources (不可变层)                     │
│         原始文档、PDF、网页、笔记——保持原样不修改             │
└─────────────────────────────────────────────────────────────┘
                              ↓ Ingest
┌─────────────────────────────────────────────────────────────┐
│                      Wiki (LLM 生成层)                        │
│     LLM 生成的摘要页、概念页、实体页——基于源文件提取           │
└─────────────────────────────────────────────────────────────┘
                              ↓ Lint
┌─────────────────────────────────────────────────────────────┐
│                    Schema (规则配置层)                      │
│           purpose.md、schema.md——定义 wiki 的结构和目的       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 三个核心操作

| 操作 | 说明 | 产出 |
|------|------|------|
| **Ingest** | 摄入新资料，LLM 自动阅读提取 | 更新的 wiki 页面、index.md、log.md |
| **Query** | 基于已编译的 wiki 回答问题 | 综合答案（带页面引用） |
| **Lint** | 健康检查，发现矛盾和孤立页面 | 修复建议、知识结构优化 |

### 2.3 文件目录结构

```
LLM Wiki 项目目录/
├── index.md              # 内容目录和 LLM 导航入口
├── log.md                # 操作记录（可解析格式）
├── overview.md           # 全局摘要（自动更新）
├── purpose.md            # Wiki 的目标、关键问题、研究范围
├── schema.md             # Wiki 的结构规则和分类
├── wiki/                 # LLM 生成的 wiki 页面
│   ├── concepts/         # 概念页面
│   ├── entities/         # 实体页面
│   └── sources/          # 源文件摘要页
├── raw/                  # 原始源文件（不可变）
│   └── sources/         # 原始文档存储
├── .llm-wiki/           # 应用状态
│   └── chats/           # 对话历史持久化
└── [[wikilink]]          # 跨页面引用语法
```

---

## 三、核心特性详解

### 3.1 两步式 Chain-of-Thought 摄取

传统方式是 LLM 读源文件直接写 wiki，LLM Wiki 将其拆分为**两步顺序 LLM 调用**：

```
Step 1 (Analysis): LLM 读取源文件 → 结构化分析
  - 关键实体、概念、论点
  - 与现有 wiki 内容的关联
  - 与现有知识的矛盾和张力
  - Wiki 结构建议

Step 2 (Generation): LLM 基于分析 → 生成 wiki 文件
  - 带 YAML frontmatter 的源摘要（type、title、sources[]）
  - 实体页面、概念页面及交叉引用
  - 更新的 index.md、log.md、overview.md
  - 人工审核项目
  - Deep Research 搜索查询
```

**增强特性**:
- **SHA256 增量缓存**: 源文件哈希对比，未变化文件自动跳过
- **持久化摄取队列**: 串行处理，队列持久化到磁盘，崩溃可恢复
- **文件夹导入**: 递归导入保留目录结构，路径作为分类上下文
- **来源追溯**: 每个 wiki 页面 YAML frontmatter 包含 `sources[]` 字段

### 3.2 4 信号知识图谱

| 信号 | 权重 | 说明 |
|------|------|------|
| **直接链接** | ×3.0 | 通过 `[[wikilinks]]` 链接的页面 |
| **来源重叠** | ×4.0 | 共享同一原始源文件（通过 frontmatter `sources[]`） |
| **Adamic-Adar** | ×1.5 | 共享公共邻居（按邻居度加权） |
| **类型亲和力** | ×1.0 | 相同页面类型的奖励（entity↔entity） |

### 3.3 Louvain 社区检测

自动发现知识聚类，基于链接拓扑而非预定义分类：

- **凝聚力评分**: Intra-edge density / (actual edges / possible edges)
- **低密度警告**: 凝聚力 < 0.15 的聚类被标记
- **12 色配色**: 聚类间视觉区分

### 3.4 Graph Insights

| 功能 | 说明 |
|------|------|
| **惊喜连接** | 跨社区边、跨类型链接、外围↔枢纽耦合 |
| **知识空白** | 孤立页面（度≤1）、稀疏社区、桥接节点（连接3+聚类） |
| **Deep Research 按钮** | 发现知识空白时触发 LLM 优化的研究 |

### 3.5 Query 检索管道

```
Phase 1: Tokenized Search
  - 英文：分词 + 停用词移除
  - 中文：CJK bigram 分词（每个 → [每个, 个…]）
  - 标题匹配加分 (+10)
  - 搜索 wiki/ 和 raw/sources/
         ↓
Phase 1.5: Vector Semantic Search (可选)
  - 通过 OpenAI 兼容 /v1/embeddings 端点 embedding
  - 存储在 LanceDB (Rust 后端)
  - 余弦相似度发现语义相关页面
         ↓
Phase 2: Graph Expansion
  - 搜索结果作为种子节点
  - 4 信号相关性模型
  - 2 跳遍历 + 衰减
         ↓
Phase 3: Budget Control
  - 可配置上下文窗口：4K → 1M tokens
  - 比例分配：60% wiki页面，20% 聊天历史，5% index，15% system
         ↓
Phase 4: Context Assembly
  - 编号页面 + 完整内容
  - System prompt 包含：purpose.md、语言规则、引用格式、index.md
  - LLM 被指示按编号引用：[1], [2]
```

**向量搜索效果**: 召回率从 58.2% 提升到 71.4%

### 3.6 Deep Research

| 特性 | 说明 |
|------|------|
| **Web 搜索** | Tavily API 提取完整内容（非截断） |
| **多查询** | LLM 在摄取时生成优化的搜索查询 |
| **LLM 优化主题** | 读取 overview.md + purpose.md 生成领域特定主题 |
| **用户确认** | 显示可编辑的主题和搜索查询供审阅 |
| **自动摄入** | 研究结果自动处理提取实体和概念 |

---

## 四、Obsidian 兼容性

LLM Wiki 生成的 wiki 目录**可直接作为 Obsidian vault 打开**：

| Obsidian 特性 | LLM Wiki 兼容性 |
|-------------|----------------|
| Markdown | ✅ 原生支持 |
| 双向链接 `[[wikilink]]` | ✅ 原生支持 |
| YAML frontmatter | ✅ 每个页面都有 |
| 图谱视图 | ✅ 可视化知识结构 |
| 标签系统 | ✅ 支持 |

### 工作流

```
LLM Wiki 生成 wiki 目录
         ↓
Obsidian 打开该目录作为 Vault
         ↓
浏览图谱视图、跟踪链接、阅读更新
         ↓ (+ Claudian)
AI 直接操作知识库内容
```

---

## 五、技术栈

| 层级 | 技术 |
|------|------|
| **桌面框架** | Tauri v2 |
| **前端** | React + TypeScript + Vite |
| **UI 框架** | Base UI + Tailwind CSS |
| **后端** | Python (FastAPI 风格) |
| **向量数据库** | LanceDB (Rust) |
| **LLM** | OpenAI 兼容 API (Claude、GLM、DeepSeek 等) |
| **图可视化** | sigma.js + graphology + ForceAtlas2 |
| **数学渲染** | KaTeX + remark-math + rehype-katex |

**开源信息**:
| 项目 | 值 |
|------|---|
| GitHub | https://github.com/nashsu/llm_wiki.git |
| 协议 | GNU General Public License (GPL) |

---

## 六、与 Hermes File Manager 的关系

| 系统 | 职责 |
|------|------|
| **Hermes File Manager** | 文件存储、团队协作、权限管理 |
| **LLM Wiki** | 知识编译、语义搜索、知识图谱 |

### 集成点

```
Hermes 空间文件
       │
       ↓ /knowledge/sync (API)
LLM Wiki 知识编译
       │
       ↓ wiki 目录
Obsidian Vault (可视化浏览)
```

---

## 七、参考资源

- [LLM Wiki 项目目录](/Users/xzmx/Downloads/my-project/llm_wiki)
- [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [Obsidian 与 LLM Wiki 的关联和区别](./01_obsidian_vs_llmwiki.md)
- [Hermes 集成方案](./03_hermes_integration.md)
