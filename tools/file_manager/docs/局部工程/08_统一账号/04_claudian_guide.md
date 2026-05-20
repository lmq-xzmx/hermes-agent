# Claudian 插件详解

> **创建日期**: 2026-05-13
> **状态**: 已完成
> **来源**: 同事收集资料整理 + 官方文档

---

## 一、插件概述

### 1.1 什么是 Claudian？

Claudian 是一款 Obsidian 社区插件，由开发者 [YishenTu](https://github.com/YishenTu/claudian) 创建，采用 MIT 开源协议。它将 Claude Code CLI 直接嵌入 Obsidian 侧边栏，让笔记库变成 AI 的工作目录。

**开源信息**:
| 项目 | 值 |
|------|---|
| GitHub | https://github.com/YishenTu/claudian |
| 协议 | MIT |
| 作者 | YishenTu |

**一句话定义**: Claudian = 把 Claude Code 搬进 Obsidian

### 1.2 核心特点对比

| 对比项 | 普通 AI 插件 | Claudian |
|--------|-------------|----------|
| **定位** | 文本生成器，一问一答 | Agent，会思考、会行动 |
| **输入方式** | 当前笔记/选中文本 | 整个 Vault 作为工作目录 |
| **跨文件操作** | 通过 RAG 读取 | 可以主动检索并写入/修改 |
| **执行过程** | 单次问答 | 多步任务推理（Goal→Plan→Act） |

---

## 二、核心功能详解

### 2.1 侧边栏聊天

点击 Obsidian 左侧栏底部的小机器人图标 🤖，即可在侧边栏打开 AI 聊天窗口，全程无需离开 Obsidian 界面。

**使用场景**:
- 随时提问，不需要切换应用
- 基于整个知识库的回答
- 长时间的任务执行

### 2.2 内联编辑（Inline Edit）

选中笔记中的一段文字，按快捷键即可让 AI 直接帮你修改，支持词级 diff 预览，确认后再生效。

**操作流程**:
```
1. 选中要修改的文字
2. 按快捷键触发内联编辑
3. AI 生成修改方案并显示 diff 预览
4. 用户确认后，修改生效
```

**优势**: 省去复制粘贴的繁琐，直接在原位修改

### 2.3 @提及任意内容

在聊天框输入 `@`，可以快速引用：

| 提及类型 | 说明 |
|---------|------|
| 笔记文件 | 引用 Vault 中的任意笔记 |
| MCP 服务器 | 引用配置好的 MCP 工具 |
| 自定义 Agent | 引用预设的 AI Agent |
| 外部目录文件 | 引用 Vault 外的文件 |

**示例**:
```
@folder/papers/deepseek-v4.pdf
@claudian
/summarize
```

### 2.4 斜杠命令 & Skills

输入 `/` 或 `$`，弹出可复用的提示词模板列表，支持自定义 Skills，且与 Claude Code 的 Skills 体系完全兼容。

**内置常用命令**:
| 命令 | 功能 |
|------|------|
| `/plan` | 切换到计划模式，让 AI 先规划后执行 |
| `/search` | 搜索知识库相关内容 |
| `/summarize` | 总结当前笔记或选中内容 |
| `/refactor` | 重构笔记结构 |

**自定义 Skills**:
```yaml
# .claude/skills/custom-skill.md
---
name: knowledge-card
description: 生成知识卡片
prompt: |
  请根据以下内容生成一张知识卡片：
  - 主题
  - 关键要点 (3-5条)
  - 相关概念
  - 实际应用
---

$SELECTED$
```

### 2.5 计划模式（Plan Mode）

按 `Shift+Tab` 切换进入计划模式。AI 会先探索你的笔记库、设计方案并展示给你看，等你批准后再执行。

**适用场景**:
- 大型任务，避免 AI 乱改一通
- 需要跨多个文件的修改
- 高风险操作前的确认

**工作流程**:
```
1. Shift+Tab 进入计划模式
2. AI 分析任务并制定计划
3. 展示计划供用户审阅
4. 用户批准后执行
5. 执行过程中可随时中断
```

### 2.6 MCP 服务器支持

支持通过 Model Context Protocol 连接外部工具，兼容三种连接方式：

| 连接方式 | 说明 | 适用场景 |
|---------|------|----------|
| **stdio** | 标准输入输出，本地进程通信 | 本地 MCP 服务 |
| **SSE** | Server-Sent Events，服务器推送 | 远程 MCP 服务 |
| **HTTP** | HTTP 请求响应 | Web API 风格的 MCP |

**MCP 配置示例**:
```json
{
  "mcpServers": {
    "hermes": {
      "command": "node",
      "args": ["/path/to/hermes-mcp.js"],
      "env": {
        "API_BASE": "http://localhost:8080/api/v1"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    }
  }
}
```

### 2.7 图片支持

可以拖拽、粘贴截图或输入图片路径，AI 能够：
- 描述图片内容
- 提取图片中的文字
- 回答关于图片的问题

---

## 三、三种权限模式

Claudian 提供了三种权限模式，控制 AI 执行操作时是否需要确认：

| 模式 | 特点 | 适用场景 |
|------|------|----------|
| **YOLO** | 全自动，AI 直接执行，不弹窗 | 日常操作、高信任任务，效率最高 |
| **Safe** | 逐步执行，每步需确认 | 重要文件修改，确保安全可控 |
| **Plan** | 先规划后执行，先看计划再放行 | 复杂/批量任务，降低风险 |

### 权限模式切换

```
设置 → Claudian → 权限模式 → 选择模式
```

### 各模式下的行为

| 模式 | 读取文件 | 写入文件 | 执行命令 | 确认对话框 |
|------|---------|---------|---------|-----------|
| YOLO | ✅ 自动 | ✅ 自动 | ✅ 自动 | ❌ 无 |
| Safe | ✅ 自动 | ⚠️ 确认 | ⚠️ 确认 | ✅ 有 |
| Plan | ✅ 自动 | 📋 显示计划 | 📋 显示计划 | ✅ 有 |

---

## 四、环境要求与安装

### 4.1 环境要求

- **Obsidian**: v1.8.9 及以上版本
- **平台**: 仅支持桌面端（macOS / Linux / Windows）
- **Claude Code CLI**: 需要安装（官方安装或 npm 安装均可）

### 4.2 安装方式

#### 方法一：手动安装（推荐）

1. 从 GitHub Releases 下载三个文件：
   - `main.js`
   - `manifest.json`
   - `styles.css`

2. 在 `.obsidian/plugins/` 目录下创建 `claudian` 文件夹

3. 将三个文件复制进去

4. 在 Obsidian → 设置 → 第三方插件中启用 Claudian

#### 方法二：BRAT 自动安装

1. 安装 BRAT 插件（Obsidian 社区插件）

2. 在 BRAT 中添加 Beta 插件，输入仓库地址：
   ```
   https://github.com/YishenTu/claudian
   ```

3. BRAT 会自动下载安装，更新也会自动通知

### 4.3 Claude Code CLI 安装

```bash
# 方式一：官方安装
# 访问 https://docs.anthropic.com/en/docs/claude-code/setup

# 方式二：npm 安装
npm install -g @anthropic-ai/claude-code

# 验证安装
claude --version
```

---

## 五、配置模型

Claudian 不限定官方 Claude，支持兼容 Anthropic API 格式的平台：

| 模型提供商 | 配置方式 |
|-----------|---------|
| Claude 官方 | ANTHROPIC_API_KEY |
| 智谱 BigModel (GLM) | ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL |
| DeepSeek | ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL |
| OpenRouter | ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL |

### 配置示例

```bash
# 环境变量配置
ANTHROPIC_API_KEY=sk-xxx...
ANTHROPIC_BASE_URL=https://api.deepseek.com/v1
```

或在插件设置界面中填写。

---

## 六、与 Claude Code 的本质区别

> **重要澄清**: Claude Code 是闭源商业产品，但Claudian 仍然可以开发，因为它是基于公开的 CLI 接口和 API工作的。

### 6.1 为什么闭源产品也能开发 Claudian？

Claudian 不依赖 Claude Code 的源码，而是依赖其公开的接口：

| 接口类型 | 说明 |
|---------|------|
| **CLI 接口** | Claude Code 提供命令行界面，Claudian 在后台调用 |
| **Anthropic API** | Claudian 也可以直接配置 API Key 调用 Claude 模型 |
| **Shell 命令执行** | 在用户电脑上执行 Bash 命令，与 Claude Code 交互 |

**类比**: Claude Code 是"引擎"，Claudian 是为这台引擎设计的"方向盘和仪表盘"。引擎的制造图纸（源码）是保密的，但操控接口（CLI/API）是公开的。

### 6.2 Claude Code 源码泄露事件

2026 年 3 月 31 日，Claude Code 的大部分源代码（超 1900 个文件、51.2 万行代码）被意外泄露，Anthropic 随后证实并进行了处理。但这不是正式开源，Claude Code 仍然是闭源商业产品。

### 6.3 Claudian vs Claude Code：本质区别

| 维度 | Claude Code | Claudian |
|------|-------------|----------|
| **本质** | 独立 AI 编程工具，是"引擎"和"核心能力" | Obsidian 插件，是"壳"和"界面" |
| **运行环境** | 独立终端工具，可在任何目录运行 | 必须安装在 Obsidian 中 |
| **核心功能** | AI 代码理解、生成、执行，计算机使用能力 | 图形化交互界面、@提及、Skills |
| **是否独立工作** | ✅ 可以独立工作 | ❌ 依赖 Claude Code 后端 |
| **用户群体** | 所有开发者 | Obsidian 用户 |

### 6.4 实际使用中的关系

```
你打开 Obsidian
    ↓
点击机器人图标 → 打开 Claudian 面板
    ↓
Claudian 在后台启动 Claude Code CLI（或通过 API 调用 Claude）
    ↓
你在 Claudian 中提问/发出指令
    ↓
Claudian 将指令传给 Claude Code
    ↓
Claude Code 执行：读文件、写笔记、搜索、运行命令
    ↓
结果返回给 Claudian，显示在侧边栏
```

**关键点**: 没有 Claude Code，Claudian 就是一个空壳——它没有任何 AI 能力。同理，没有 Claudian，Claude Code 仍然可以通过终端独立工作。

```
┌─────────────────────────────────────────────────────────────┐
│                      Obsidian                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                    Claudian 插件                      │  │
│  │  - 侧边栏 UI                                         │  │
│  │  - 内联编辑                                          │  │
│  │  - @提及支持                                         │  │
│  │  - Skills 集成                                       │  │
│  └───────────────────────┬─────────────────────────────┘  │
│                          │                                │
│                          ↓                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │               Claude Code CLI                       │  │
│  │  - 实际的 AI 引擎                                    │  │
│  │  - 文件读写能力                                      │  │
│  │  - 终端命令执行                                      │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Claudian vs Claude Code CLI

| 维度 | Claude Code CLI | Claudian |
|------|----------------|----------|
| **界面** | 终端命令行 | Obsidian 侧边栏 |
| **上下文** | 当前工作目录 | 整个 Obsidian Vault |
| **交互方式** | 终端输入输出 | 所见即所得 UI |
| **文件操作** | 命令行 | 点击/选中触发 |
| **双链支持** | 无 | 原生支持 `[[wikilink]]` |

---

## 七、常用快捷键

| 快捷键 | 功能 |
|--------|------|
| `Shift+Tab` | 切换到计划模式 |
| `Cmd/Ctrl+Shift+E` | 内联编辑选中内容 |
| `/` | 弹出斜杠命令列表 |
| `$` | 弹出 Skills 列表 |
| `@` | 弹出提及列表 |
| `Cmd/Ctrl+L` | 打开侧边栏聊天 |

---

## 八、故障排除

### 8.1 Claude Code CLI 未找到

```
错误: "Claude Code CLI is not installed"
解决:
1. npm install -g @anthropic-ai/claude-code
2. 重启 Obsidian
```

### 8.2 API 请求失败

```
错误: "API request failed"
解决:
1. 检查 ANTHROPIC_API_KEY 是否正确
2. 检查网络连接
3. 确认 API 余额充足
```

### 8.3 MCP 连接失败

```
错误: "MCP server connection failed"
解决:
1. 检查 MCP 服务器是否运行
2. 确认端口和路径配置正确
3. 查看 MCP 服务器日志
```

---

## 九、相关文档

- [Obsidian 与 LLM Wiki FM 的关联和区别](./01_obsidian_vs_llmwiki.md)
- [为什么还需要 Claudian](./02_why_claudian.md)
- [Hermes 集成方案](./03_hermes_integration.md)
