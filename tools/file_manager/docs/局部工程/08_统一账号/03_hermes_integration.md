# Hermes 与 Obsidian 生态集成方案

> **创建日期**: 2026-05-13
> **状态**: 规划中
> **相关项目**: Hermes File Manager, LLM Wiki, Obsidian, Claudian

---

## 一、集成背景

### 1.1 三个系统的定位

| 系统 | 定位 | 核心职责 |
|------|------|----------|
| **Hermes File Manager** | 文件存储与协作平台 | 文件管理、团队协作、权限管理、生命周期约束 |
| **LLM Wiki** | 知识编译与维护系统 | 文档知识化、语义搜索、知识图谱、Deep Research |
| **Obsidian + Claudian** | 知识浏览与 AI 操作界面 | 可视化浏览、笔记管理、AI 驱动的工作流 |

### 1.2 集成的核心价值

```
Hermes (文件层) → LLM Wiki (知识层) → Obsidian + Claudian (应用层)

数据流向:
1. 用户在 Hermes 中管理文件（上传、分享、协作）
2. 文件同步到 LLM Wiki 进行知识编译
3. 生成的知识库在 Obsidian 中可视化浏览
4. Claudian 让 AI 直接操作知识库内容
```

---

## 二、集成方案

### 2.1 方案一：知识同步管道（推荐）

```
Hermes 空间文件
       │
       ↓ /knowledge/sync
LLM Wiki (知识编译)
       │
       ↓ wiki 目录
Obsidian Vault (直接打开)
       │
       ↓ Claudian
AI 操作（内联编辑、@提及、Skills）
```

**优点**:
- Hermes 作为文件存储层，提供协作和权限管理
- LLM Wiki 负责知识化，Obsidian 负责可视化
- Claudian 提供 AI 操作能力

**限制**:
- 单向同步（Hermes → LLM Wiki → Obsidian）
- 需要手动触发同步

### 2.2 方案二：MCP Server 方案

将 Hermes File Manager 实现为 MCP Server，让 Claudian 可以直接调用 Hermes 的文件操作能力：

```typescript
// Hermes MCP Server Tool Definitions
{
  name: "hermes-file-manager",
  tools: [
    {
      name: "list_spaces",
      description: "列出当前用户的所有 Hermes 空间"
    },
    {
      name: "list_files",
      description: "列出指定空间中的文件",
      arguments: { space_id: "string", path: "string" }
    },
    {
      name: "upload_file",
      description: "上传文件到指定空间",
      arguments: { space_id: "string", path: "string", file: "blob" }
    },
    {
      name: "get_file_content",
      description: "获取文件内容",
      arguments: { space_id: "string", path: "string" }
    },
    {
      name: "search_knowledge",
      description: "搜索知识库",
      arguments: { query: "string", project: "string" }
    },
    {
      name: "sync_to_knowledge",
      description: "同步文件到知识库",
      arguments: { source_path: "string", project: "string" }
    }
  ]
}
```

**优点**:
- Claudian 可以直接调用 Hermes 的文件操作
- AI 可以读写 Hermes 空间中的文件
- 真正的双向联动

**限制**:
- 需要开发 MCP Server适配层
- 需要处理认证和权限

### 2.3 方案三：文件系统桥接

通过文件系统路径直接关联 Hermes 存储和 Obsidian Vault：

```
Hermes 存储路径 (例如: ~/Library/Containers/com.hermes/)
       ↓ 符号链接或绑定挂载
Obsidian Vault (直接读取 Hermes 管理的文件)
```

**优点**:
- 最简单，无需额外开发
- Obsidian 直接访问 Hermes 文件

**限制**:
- 依赖特定存储路径
- 不支持远程 Hermes 存储

---

## 三、实际工作流设计

### 3.1 日常知识积累工作流

```
1. 用户在 Hermes 中上传文档（PDF、Markdown、文本等）
         ↓
2. 触发 /knowledge/sync，LLM Wiki 自动处理
         ↓
3. LLM Wiki 生成 wiki 页面（摘要、概念、实体）
         ↓
4. 用户在 Obsidian 中打开 LLM Wiki 目录作为 Vault
         ↓
5. 使用 Claudian 询问知识库内容、让 AI 整理笔记
```

### 3.2 AI 辅助写作工作流

```
1. 用户在 Obsidian 中创建或编辑笔记
         ↓
2. 使用 Claudian 内联编辑功能选中文字
         ↓
3. AI 直接修改并更新笔记（带 diff 预览）
         ↓
4. 有价值的回答可以"Save to Wiki"归档到 LLM Wiki
         ↓
5. LLM Wiki 自动提取实体和概念，更新知识网络
```

---

## 四、技术实现要点

### 4.1 Hermes → LLM Wiki 同步

```python
# server.py 中的同步端点
@app.post("/api/v1/knowledge/sync")
async def sync_to_knowledge(
    source_path: str,
    project: str = "default"
):
    """同步 Hermes 空间文件到 LLM Wiki"""
    # 1. 获取 Hermes 空间中的文件
    # 2. 调用 LLM Wiki 的摄取 API
    # 3. 返回同步状态
```

### 4.2 Claudian MCP 集成

```typescript
// claudian MCP 配置示例
{
  mcpServers: {
    hermes: {
      command: "node",
      args: ["/path/to/hermes-mcp-server.js"],
      env: {
        API_BASE: "http://localhost:8080/api/v1"
      }
    }
  }
}
```

---

## 五、下一步行动

- [ ] 评估技术方案可行性
- [ ] 设计 Hermes MCP Server API
- [ ] 实现文件同步管道
- [ ] 编写 Claudian 插件原型
- [ ] 测试完整工作流

---

## 六、相关文档

- [Obsidian 与 LLM Wiki FM 的关联和区别](./01_obsidian_vs_llmwiki.md)
- [Claudian 插件详解](./02_why_claudian.md)
