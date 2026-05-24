# Claudian Hermes MCP 插件技术设计

> **创建日期**: 2026-05-20
> **状态**: 设计完成
> **目标**: 实现 Claudian → Hermes → LLM Wiki 调用链路

---

## 一、背景与目标

### 1.1 当前架构

```
Claudian（Obsidian 插件）
    ↓ MCP（无连接）
    ❌
Hermes File Manager
    ↓ webhook（已实现）
LLM Wiki
```

**问题**：Claudian 与 Hermes/LLM Wiki 之间无集成链路，Claudian 无法直接触发 LLM Wiki 处理。

### 1.2 目标架构

```
Claudian（Obsidian 插件）
    ↓ MCP
hermes-mcp（Node.js MCP Server）← 新开发
    ↓ HTTP API
Hermes File Manager
    ↓ webhook（已实现）
LLM Wiki
```

### 1.3 核心能力

| 功能 | 描述 |
|------|------|
| **sync_to_wiki** | 触发文件同步到 LLM Wiki |
| **search_wiki** | 语义搜索知识库 |
| **get_sync_status** | 获取同步状态 |
| **list_spaces** | 列出用户可访问的 Space |

---

## 二、技术方案

### 2.1 技术栈

| 组件 | 技术选型 | 原因 |
|------|---------|------|
| **MCP Server** | TypeScript + Node.js | 与 Hermes Tauri 配置一致 |
| **MCP SDK** | @modelcontextprotocol/sdk | 官方标准库 |
| **HTTP Client** | ky 或 fetch | 轻量、TypeScript 友好 |
| **配置存储** | JSON 文件 | 简单、无额外依赖 |

### 2.2 项目结构

```
tools/
└── claudian_hermes_plugin/              # 项目根目录
    ├── package.json                     # 依赖管理
    ├── tsconfig.json                    # TypeScript 配置
    ├── src/
    │   ├── index.ts                     # 入口，导出 MCP Server
    │   ├── server.ts                    # MCP Server 主逻辑
    │   ├── tools/
    │   │   ├── sync_to_wiki.ts          # 同步到 Wiki
    │   │   ├── search_wiki.ts           # 搜索 Wiki
    │   │   ├── get_sync_status.ts       # 同步状态
    │   │   └── list_spaces.ts           # 列出 Spaces
    │   ├── api/
    │   │   └── hermes_client.ts         # Hermes API 客户端
    │   └── types.ts                     # 类型定义
    ├── README.md                        # 安装说明
    └── config.example.json              # 配置示例
```

### 2.3 MCP 协议实现

根据 Claudian 文档支持的三种 MCP 连接方式：

| 方式 | 说明 | 选择 |
|------|------|------|
| **stdio** | 标准输入输出，本地进程通信 | ✅ 用于本地开发 |
| **SSE** | Server-Sent Events，服务器推送 | 预留 |
| **HTTP** | HTTP 请求响应 | 预留 |

**优先实现 stdio 模式**，最简单可靠。

---

## 三、API 接口设计

### 3.1 Hermes API 端点（已有）

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/spaces` | GET | 列出用户 Spaces |
| `/api/v1/spaces/{space_id}/sync/delta` | POST | 触发同步 delta |
| `/api/v1/spaces/{space_id}/sync/status` | GET | 获取同步状态 |
| `/knowledge/search` | GET | LLM Wiki 语义搜索 |

### 3.2 MCP Tools 接口

```typescript
// MCP Server 暴露的工具列表
const tools = [
  {
    name: "list_spaces",
    description: "列出用户可访问的所有 Space",
    inputSchema: {
      type: "object",
      properties: {}
    }
  },
  {
    name: "sync_to_wiki",
    description: "同步文件到 LLM Wiki",
    inputSchema: {
      type: "object",
      properties: {
        space_id: { type: "string", description: "目标 Space ID" },
        file_path: { type: "string", description: "要同步的文件路径" }
      },
      required: ["space_id", "file_path"]
    }
  },
  {
    name: "search_wiki",
    description: "语义搜索 LLM Wiki",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "搜索query" },
        space_id: { type: "string", description: "Space ID" },
        limit: { type: "number", description: "返回数量", default: 10 }
      },
      required: ["query", "space_id"]
    }
  },
  {
    name: "get_sync_status",
    description: "获取同步状态",
    inputSchema: {
      type: "object",
      properties: {
        space_id: { type: "string", description: "Space ID" }
      },
      required: ["space_id"]
    }
  }
]
```

---

## 四、核心实现

### 4.1 Hermes Client

```typescript
// src/api/hermes_client.ts
import { z } from 'zod';

const SpaceSchema = z.object({
  id: z.string(),
  name: z.string(),
  team_id: z.string(),
  quota_bytes: z.number(),
  used_bytes: z.number()
});

const SyncStatusSchema = z.object({
  space_id: z.string(),
  last_sync: z.string().nullable(),
  pending_files: z.number(),
  status: z.enum(['idle', 'syncing', 'error'])
});

export class HermesClient {
  constructor(private baseUrl: string, private token: string) {}

  async listSpaces(): Promise<z.infer<typeof SpaceSchema>[]> {
    const res = await fetch(`${this.baseUrl}/api/v1/spaces`, {
      headers: { Authorization: `Bearer ${this.token}` }
    });
    return res.json();
  }

  async syncToWiki(spaceId: string, filePath: string): Promise<void> {
    await fetch(`${this.baseUrl}/api/v1/spaces/${spaceId}/sync/delta`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ file_path: filePath })
    });
  }

  async getSyncStatus(spaceId: string): Promise<z.infer<typeof SyncStatusSchema>> {
    const res = await fetch(`${this.baseUrl}/api/v1/spaces/${spaceId}/sync/status`, {
      headers: { Authorization: `Bearer ${this.token}` }
    });
    return res.json();
  }

  async searchWiki(query: string, project: string, limit = 10): Promise<any[]> {
    const res = await fetch(
      `${this.baseUrl}/knowledge/search?query=${encodeURIComponent(query)}&project=${encodeURIComponent(project)}&limit=${limit}`,
      { headers: { Authorization: `Bearer ${this.token}` } }
    );
    return res.json();
  }
}
```

### 4.2 MCP Server 主逻辑

```typescript
// src/server.ts
import { MCPServer } from '@modelcontextprotocol/sdk/server';
import { StreamableSSEServerTransport } from '@modelcontextprotocol/sdk/server/sse';
import { HermesClient } from './api/hermes_client';
import { listSpaces } from './tools/list_spaces';
import { syncToWiki } from './tools/sync_to_wiki';
import { searchWiki } from './tools/search_wiki';
import { getSyncStatus } from './tools/get_sync_status';

export function createHermesMCPServer(config: { baseUrl: string; token: string }) {
  const hermes = new HermesClient(config.baseUrl, config.token);

  const server = new MCPServer({
    name: 'hermes-mcp',
    version: '1.0.0',
    tools: [listSpaces, searchWiki, syncToWiki, getSyncStatus].map(t => ({
      ...t,
      handler: async (args) => t.handler(args, hermes)
    }))
  });

  return server;
}
```

### 4.3 入口文件

```typescript
// src/index.ts
import { createHermesMCPServer } from './server';
import * as fs from 'fs';
import * as path from 'path';

const configPath = path.join(process.env.HOME, '.config', 'hermes-mcp', 'config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));

const server = createHermesMCPServer(config);
server.start();
```

---

## 五、配置管理

### 5.1 配置文件

```json
// ~/.config/hermes-mcp/config.json
{
  "hermes": {
    "base_url": "http://localhost:8080/api/v1",
    "token": "your-jwt-token-here"
  },
  "mcp": {
    "transport": "stdio"
  }
}
```

### 5.2 认证流程

1. 用户在 File Manager Web 界面获取 JWT Token
2. 将 Token 配置到 `~/.config/hermes-mcp/config.json`
3. MCP Server 启动时加载配置

### 5.3 Token 获取方式（待补充）

| 方式 | 说明 |
|------|------|
| 手动复制 | Web 界面显示 Token，用户手动复制 |
| OAuth 授权 | Claudian 内置登录流程（未来扩展） |

---

## 六、Claudian 配置

### 6.1 MCP 配置

在 Claudian 设置中添加 MCP Server：

```json
{
  "mcpServers": {
    "hermes": {
      "command": "node",
      "args": ["/path/to/hermes-mcp/dist/index.js"],
      "env": {}
    }
  }
}
```

### 6.2 使用方式

用户可以在 Claudian 中：

```
@sync_to_wiki
/sync wiki --space-id xxx --file-path /path/to/note.md
```

或在聊天中直接调用：
```
请把这个笔记同步到 LLM Wiki
```

---

## 七、错误处理

### 7.1 错误类型

| 错误码 | 说明 | 处理方式 |
|--------|------|---------|
| `UNAUTHORIZED` | Token 无效或过期 | 提示用户重新配置 Token |
| `SPACE_NOT_FOUND` | Space 不存在 | 返回错误，提示检查 Space ID |
| `SYNC_IN_PROGRESS` | 同步正在进行 | 返回当前状态 |
| `NETWORK_ERROR` | 网络连接失败 | 重试 3 次后返回错误 |

### 7.2 日志

```typescript
// 日志输出到 stderr，供用户排查
console.error('[hermes-mcp]', new Date().toISOString(), error);
```

---

## 八、部署方式

### 8.1 开发模式

```bash
cd tools/claudian_hermes_plugin
npm install
npm run build
```

### 8.2 预编译分发

```json
// package.json
{
  "scripts": {
    "build": "tsc",
    "package": "npm run build && tar -czf hermes-mcp.tar.gz dist/ README.md"
  }
}
```

### 8.3 安装路径

| 平台 | 推荐路径 |
|------|---------|
| macOS | `~/.config/hermes-mcp/` |
| Linux | `~/.config/hermes-mcp/` |
| Windows | `%APPDATA%/hermes-mcp/` |

---

## 九、安装指南

### 9.1 前置要求

| 要求 | 版本 | 说明 |
|------|------|------|
| Node.js | ≥ 18.0 | MCP Server 运行环境 |
| npm | ≥ 9.0 | 包管理 |
| Hermes File Manager | 运行中 | 后端服务 |
| Obsidian | ≥ 1.8.9 | 笔记软件 |
| Claudian | 最新版 | Obsidian 插件 |

### 9.2 安装步骤

#### 第一步：部署 Hermes File Manager 后端

**方式 A：Python 服务（开发模式）**
```bash
cd tools/file_manager
python server.py
# 服务运行在 http://localhost:8080
```

**方式 B：Tauri Desktop App**
```bash
cd tools/file_manager
cargo tauri dev
# 服务运行在 http://localhost:18424
```

#### 第二步：创建配置目录

```bash
mkdir -p ~/.config/hermes-mcp
```

#### 第三步：编译 hermes-mcp

```bash
cd tools/claudian_hermes_plugin
npm install
npm run build
```

#### 第四步：配置 JWT Token

```bash
nano ~/.config/hermes-mcp/config.json
```

```json
{
  "hermes": {
    "base_url": "http://localhost:8080/api/v1",
    "token": "your-jwt-token-here"
  },
  "mcp": {
    "transport": "stdio"
  }
}
```

**Token 获取方式**：

方式 1：Web 界面
1. 打开 http://localhost:5173
2. 登录账号
3. 打开开发者工具（F12）→ Application → Local Storage → 复制 token

方式 2：API 登录
```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "yourpassword"}'
```

#### 第五步：配置 Claudian MCP Server

1. 打开 Obsidian → 设置 → 第三方插件 → 启用 Claudian
2. Claudian 设置 → MCP Servers → 添加：

```json
{
  "mcpServers": {
    "hermes": {
      "command": "node",
      "args": ["/absolute/path/to/hermes-mcp/dist/index.js"],
      "env": {}
    }
  }
}
```

**路径示例**：
- macOS: `/Users/用户名/projects/hermes-agent/tools/claudian_hermes_plugin/dist/index.js`
- Linux: `/home/用户名/projects/hermes-agent/tools/claudian_hermes_plugin/dist/index.js`

#### 第六步：验证安装

在 Obsidian 中打开 Claudian 侧边栏，尝试：

```
@hermes list-spaces
```

如果返回 Space 列表，说明安装成功。

### 9.3 端口对照表

| 部署方式 | 端口 | base_url 配置 |
|---------|------|--------------|
| Python server.py | 8080 | `http://localhost:8080/api/v1` |
| Tauri dev | 18424 | `http://localhost:18424/api/v1` |
| Tauri build | 8080 | `http://localhost:8080/api/v1` |

### 9.4 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| MCP 连接失败 | 路径错误 | 使用绝对路径，确认 dist/index.js 存在 |
| 401 Unauthorized | Token 过期 | 重新获取 Token 并更新 config.json |
| Connection refused | 后端未启动 | 确认 Hermes File Manager 服务运行中 |
| Space not found | space_id 错误 | 先用 `list-spaces` 查看正确的 ID |

---

## 十、测试计划

### 9.1 单元测试

| 测试项 | 工具 |
|--------|------|
| HermesClient API 调用 | jest + nock |
| Tool 参数验证 | zod |

### 9.2 集成测试

| 测试项 | 说明 |
|--------|------|
| MCP stdio 通信 | 启动 Server，模拟 Claudian 请求 |
| 端到端同步 | File Manager + LLM Wiki 完整链路 |

---

## 十、相关文档

- [Claudian 插件详解](../08_统一账号/04_claudian_guide.md) — Claudian MCP 配置说明
- [技术实现路线图](./03_技术实现路线图.md) — Phase 2 任务分解
- [Hermes 集成方案](../08_统一账号/03_hermes_integration.md) — Hermes 生态概览

---

## 附录 A：MCP 协议参考

### A.1 工具调用协议

```
Request (Claudian → hermes-mcp):
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "sync_to_wiki",
    "arguments": {
      "space_id": "space_xxx",
      "file_path": "/notes/test.md"
    }
  }
}

Response (hermes-mcp → Claudian):
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "已同步 3 个文件到 LLM Wiki"
      }
    ]
  }
}
```

### A.2 工具列表协议

```
Request:
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}

Response:
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      { "name": "sync_to_wiki", "description": "...", "inputSchema": {...} },
      { "name": "search_wiki", "description": "...", "inputSchema": {...} }
    ]
  }
}
```