# Hermes MCP Server

MCP Server for Hermes File Manager - 提供 Claudian 与 LLM Wiki 的集成。

## 功能

- **list_spaces** - 列出用户可访问的所有 Space
- **sync_to_wiki** - 同步文件到 LLM Wiki
- **search_wiki** - 语义搜索 LLM Wiki 知识库
- **get_sync_status** - 获取同步状态

## 系统要求

- Node.js >= 18.0.0
- Hermes File Manager 后端运行中
- Obsidian + Claudian 插件

## 安装

### 1. 编译

```bash
cd tools/claudian_hermes_plugin
npm install
npm run build
```

### 2. 配置

创建 `~/.config/hermes-mcp/config.json`：

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

**Token 获取**：登录 Hermes File Manager Web，打开开发者工具 → Application → Local Storage → 复制 token

### 3. 配置 Claudian

Obsidian → 设置 → Claudian → MCP Servers：

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

## 使用

在 Claudian 中：

```
@hermes list-spaces
@hermes sync-to-wiki --space-id xxx --file-path /notes/test.md
@hermes search-wiki --query "LLM 架构" --space-id xxx
```

## 端口对照

| 部署方式 | 端口 |
|---------|------|
| Python server.py | 8080 |
| Tauri dev | 18424 |
| Tauri build | 8080 |

## 开发

```bash
npm run watch  # 监听模式
npm test       # 测试
```