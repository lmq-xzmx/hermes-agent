# Claudian 客户端集成方案

> **创建日期**: 2026-05-21
> **状态**: 开发完成
> **相关项目**: Hermes File Manager, LLM Wiki, Claudian, hermes-mcp

---

## 一、方案概述

### 1.1 集成目标

让 Claudian（Obsidian 插件）通过 MCP 协议直连 Hermes File Manager，实现：
- 在 Obsidian 侧边栏直接查询团队知识库
- 触发知识同步到 LLM Wiki
- 查看同步状态和管理 Space

### 1.2 核心组件

| 组件 | 角色 | 位置 |
|------|------|------|
| **Claudian** | Obsidian 插件，AI 对话界面 | Obsidian 社区插件 |
| **hermes-mcp** | MCP Server，Hermes API 桥接 | `tools/claudian_hermes_plugin/` |
| **Hermes File Manager** | 后端服务，SSO + RBAC | `tools/file_manager/` |
| **LLM Wiki** | 知识编译引擎 | `llm_wiki_FM/` |

### 1.3 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Obsidian                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      Claudian 插件                         │  │
│  │  - 侧边栏聊天                                              │  │
│  │  - @提及 MCP 工具                                          │  │
│  │  - 内联编辑 /plan /query 等 Skills                         │  │
│  └────────────────────────────┬──────────────────────────────┘  │
└───────────────────────────────┼──────────────────────────────────┘
                                │ MCP (stdio)
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│                      hermes-mcp (Node.js)                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  MCP Server                                                │  │
│  │  - list_spaces      → GET /api/v1/spaces                  │  │
│  │  - sync_to_wiki     → POST /api/v1/knowledge/sync         │  │
│  │  - search_wiki      → GET /api/v1/knowledge/search        │  │
│  │  - get_sync_status  → GET /api/v1/spaces/{id}/sync/status │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬──────────────────────────────────┘
                                │ HTTP + JWT
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│                    Hermes File Manager (Python)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Auth API    │  │  Space API   │  │  Knowledge API       │  │
│  │  /auth/*     │  │  /spaces/*   │  │  /knowledge/*        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  RBAC 权限验证 → JWT Token 验证 → 团队数据隔离                   │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ↓ LLM Wiki 处理
                      ┌──────────────────────┐
                      │      LLM Wiki        │
                      │  wiki/（团队隔离）    │
                      └──────────────────────┘
```

---

## 二、hermes-mcp 已实现功能

### 2.1 MCP Tools 清单

| 工具 | 功能 | 验证状态 | 说明 |
|------|------|---------|------|
| `list_spaces` | 列出用户可访问的 Space | ✅ 已验证 | JWT 认证，返回 Space 列表 |
| `sync_to_wiki` | 同步文件到 LLM Wiki | ✅ 已验证 | 调用 `/knowledge/sync` |
| `search_wiki` | 语义搜索知识库 | ✅ 已验证 | 调用 `/knowledge/search` |
| `get_sync_status` | 获取同步状态 | ✅ 已验证 | 调用 `/spaces/{id}/sync/status` |

### 2.2 项目结构

```
tools/claudian_hermes_plugin/
├── package.json              # 依赖：@modelcontextprotocol/sdk ^1.0.0, zod ^3.23.0
├── tsconfig.json              # TypeScript 配置
├── README.md                  # 安装说明
├── config.example.json        # 配置示例
├── src/
│   ├── index.ts               # 入口，配置文件加载
│   ├── server.ts              # MCP Server 主逻辑
│   ├── types.ts               # 类型定义
│   ├── api/
│   │   └── hermes_client.ts   # Hermes API 客户端
│   └── tools/
│       ├── list_spaces.ts     # 列出 Spaces
│       ├── sync_to_wiki.ts    # 同步到 Wiki
│       ├── search_wiki.ts     # 搜索 Wiki
│       └── get_sync_status.ts # 同步状态
└── dist/                      # 编译输出（npm run build）
```

### 2.3 验证测试记录

```bash
# list_spaces 测试
$ echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_spaces","arguments":{}}}' | node dist/index.js
{"result":{"content":[{"type":"text","text":"共 1 个 Space：\n\n1. **测试 Space** (ID: `bad67c4e-503d-43ed-ac89-86e3e2ebc03e`)"}]},"jsonrpc":"2.0","id":3}

# get_sync_status 测试
$ echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"get_sync_status","arguments":{"space_id":"bad67c4e-503d-43ed-ac89-86e3e2ebc03e"}}}' | node dist/index.js
{"result":{"content":[{"type":"text","text":"✅ 同步状态：\n- Space: `bad67c4e-503d-43ed-ac89-86e3e2ebc03e`\n- 状态: idle\n- 最后同步: 从未同步"}]},"jsonrpc":"2.0","id":4}
```

---

## 三、安装与配置

### 3.1 前置条件

- **Obsidian** v1.8.9+
- **Claude Code CLI**（用于 YOLO/Plan 模式）
- **hermes-mcp** 已编译（`npm run build`）

### 3.2 步骤一：编译 hermes-mcp

```bash
cd tools/claudian_hermes_plugin
npm install
npm run build
```

### 3.3 步骤二：配置 hermes-mcp

创建配置文件 `~/.config/hermes-mcp/config.json`：

```json
{
  "hermes": {
    "base_url": "http://localhost:8080",
    "token": "YOUR_JWT_TOKEN_HERE"
  },
  "mcp": {
    "transport": "stdio"
  }
}
```

**获取 Token**：
1. 登录 Hermes File Manager Web
2. 打开浏览器开发者工具 → Application → Local Storage
3. 复制 `authStore` 中的 `access_token`

### 3.4 步骤三：配置 Claudian

在 Obsidian 中打开 Claudian 设置，找到 MCP Server 配置：

```json
{
  "mcpServers": {
    "hermes": {
      "command": "node",
      "args": ["/FULL/PATH/TO/hermes-mcp/dist/index.js"],
      "env": {}
    }
  }
}
```

或者手动编辑 `.obsidian/plugins/claudian/config.json`：

```json
{
  "mcpServers": {
    "hermes": {
      "command": "node",
      "args": ["/Users/xzmx/Downloads/my-project/hermes-agent/tools/claudian_hermes_plugin/dist/index.js"],
      "env": {}
    }
  }
}
```

### 3.5 步骤四：验证集成

1. 重启 Obsidian
2. 点击侧边栏 Claudian 图标
3. 输入 `@hermes` 应该能看到自动补全
4. 尝试输入 `@hermes list-spaces`

---

## 四、使用方式

### 4.1 在 Claudian 侧边栏使用 MCP 工具

```
@hermes list-spaces                                    # 列出所有可访问 Space
@hermes sync-to-wiki --space-id xxx --file-path /notes/test.md   # 同步文件到 Wiki
@hermes search-wiki --query "项目架构" --space-id xxx            # 搜索知识库
@hermes get-sync-status --space-id xxx                         # 查看同步状态
```

### 4.2 组合使用示例

**日常知识查询**：
```
@hermes search-wiki --query "Hermes 系统架构" --space-id <your-space-id>
```

**同步新笔记到知识库**：
```
@hermes sync-to-wiki --space-id <your-space-id> --file-path /notes/meeting-2026-05-21.md
```

**查看同步状态**：
```
@hermes get-sync-status --space-id <your-space-id>
```

### 4.3 与 /ingest /query /lint 配合

```
# 先查询知识库
@hermes search-wiki --query "最新的产品需求" --space-id xxx

# Claudian 执行 /ingest 摄入新资料
/ingest "新的产品需求文档"

# Claudian 执行 /query 基于知识库回答
/query "基于当前知识库，总结项目进展"

# Claudian 执行 /lint 健康检查
/lint
```

---

## 五、权限模型

### 5.1 JWT Token 中的权限信息

```json
{
  "sub": "user_uuid",
  "username": "alice",
  "teams": ["team_hermes", "team_research"],
  "roles": {"team_hermes": "admin", "team_research": "viewer"},
  "type": "access"
}
```

### 5.2 RBAC 角色

| 角色 | list_spaces | sync_to_wiki | search_wiki | get_sync_status |
|------|-------------|--------------|-------------|-----------------|
| **admin** | ✅ 全部 | ✅ 全部 | ✅ 全部 | ✅ 全部 |
| **editor** | ✅ 所属团队 | ✅ 所属团队 | ✅ 所属团队 | ✅ 所属团队 |
| **viewer** | ✅ 所属团队 | ❌ | ✅ 所属团队 | ✅ 所属团队 |

### 5.3 数据隔离

- Space 按 `team_id` 隔离
- 用户只能访问其所属团队的 Space
- LLM Wiki wiki 目录按 `team_{team_id}` 划分

---

## 六、与 SyncWebhookCaller 的关系

### 6.1 两个触发路径

| 组件 | 触发方式 | 场景 |
|------|---------|------|
| **SyncWebhookCaller** | 自动（同步后） | File Manager 文件变更自动触发 LLM Wiki 处理 |
| **hermes-mcp sync_to_wiki** | 手动（MCP 调用） | 用户主动在 Claudian 触发同步 |

### 6.2 何时用哪个

| 场景 | 推荐方式 |
|------|---------|
| Obsidian 中编辑了笔记，想同步到 Wiki | `@hermes sync-to-wiki` |
| File Manager Web 上传了文件 | SyncWebhookCaller 自动处理 |
| 想查询同步历史 | `@hermes get-sync-status` |
| 批量同步多个文件 | 多次调用 `@hermes sync-to-wiki` |

---

## 七、安全考虑

### 7.1 Token 安全

| 措施 | 说明 |
|------|------|
| **Token 存储** | 保存在 `~/.config/hermes-mcp/config.json`，确保文件权限 `600` |
| **不提交到 Git** | 确认 `.gitignore` 包含该配置文件 |
| **定期更换** | Token 过期前重新获取 |

### 7.2 权限控制

| 原则 | 应用 |
|------|------|
| **最小权限** | 新用户默认 `limited_access`，需要 Admin 分配权限 |
| **逐步信任** | 先用 viewer 测试，确认正常后再给 editor 权限 |
| **审计日志** | 所有操作记录在 File Manager 审计日志中 |

### 7.3 Claude Code 权限模式

Claudian 提供三种权限模式，建议：

| 模式 | 适用场景 | 风险 |
|------|---------|------|
| **YOLO** | 熟悉的操作、完全信任 | 高（自动执行所有命令） |
| **Safe** | 日常使用 | 中（写入操作需确认） |
| **Plan** | 不熟悉的操作、高风险任务 | 低（先看计划再执行） |

---

## 八、故障排除

### 8.1 Claudian 无法连接 hermes-mcp

```bash
# 检查 hermes-mcp 是否运行
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | node dist/index.js

# 检查配置文件路径
# macOS: ~/.config/hermes-mcp/config.json
# Linux: ~/.config/hermes-mcp/config.json
# Windows: %APPDATA%/hermes-mcp/config.json
```

### 8.2 API 请求失败 (401 Unauthorized)

```bash
# Token 过期，需要重新获取
# 1. 登录 Hermes File Manager
# 2. 获取新的 access_token
# 3. 更新配置文件
```

### 8.3 Space 列表为空

```bash
# 可能原因：
# 1. 用户不属于任何团队
# 2. Token 中没有 teams 字段
# 3. 团队没有创建 Space

# 解决：联系 Admin 创建 Space 并分配权限
```

### 8.4 sync_to_wiki 失败

```bash
# 检查 LLM Wiki 服务是否运行
curl http://localhost:8080/api/v1/knowledge/health

# 检查 Webhook 配置是否正确
# 环境变量: SYNC_TRIGGER_WIKI=true
```

---

## 九、相关文档

- [07_模块整合方案总结](./07_模块整合方案总结.md) — 模块整合架构总览
- [06_claudian_hermes_plugin.md](../08_统一账号/06_claudian_hermes_plugin.md) — hermes-mcp 详细设计
- [04_claudian_guide.md](../08_统一账号/04_claudian_guide.md) — Claudian 插件详解
- [05_llmwiki_detail.md](../08_统一账号/05_llmwiki_detail.md) — LLM Wiki 技术细节