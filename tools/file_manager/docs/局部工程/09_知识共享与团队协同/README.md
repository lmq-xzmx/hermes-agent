# 知识共享与团队协同设计方案

> **创建日期**: 2026-05-18
> **状态**: 规划中
> **相关项目**: Hermes File Manager, LLM Wiki, OpenHuman, Obsidian, Claudian, Hermes 主系统

---

## 一、现状分析

### 1.1 各系统能力边界

| 系统 | 服务对象 | 知识管理 | 团队协作 | 认证机制 |
|------|---------|---------|---------|---------|
| **OpenHuman** | 个人用户 | Memory Tree（浅） | ❌ 无 | 本地账号 |
| **Hermes 主系统** | 个人用户 | ❌ 无 | ❌ 无 | 平台 Pairing |
| **Hermes File Manager** | 团队 | LLM Wiki 同步 | ✅ 完整 RBAC | JWT 用户认证 |
| **LLM Wiki** | 个人/团队 | 深度编译（三层架构） | ❌ 无 | 信任调用方 |
| **Obsidian + Claudian** | 个人用户 | 本地 Vault | ❌ 无法网络共享 | 本地 |

### 1.2 知识共享的核心障碍

| 问题 | 说明 |
|------|------|
| **LLM Wiki 无认证** | 目前信任调用方传入的 `user_id`，无法区分团队成员权限 |
| **Obsidian 本地 Vault** | Vault 在本地，团队成员无法同时访问同一个 Vault |
| **OpenHuman 个人定位** | Memory Tree 是个人的，团队化需要较大改动 |
| **链路断裂** | File Manager → LLM Wiki → Obsidian 的链缺少团队权限层 |

---

## 二、系统定位与数据流

### 2.1 各系统角色定义

```
┌─────────────────────────────────────────────────────────────────┐
│                        OpenHuman                                │
│   个人 AI 超级助手 · auto-fetch · 118+ 集成 · Memory Tree       │
│                         (个人前端)                              │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Hermes 主系统                              │
│            消息路由中枢 · MCP Server · Session 管理              │
│                       (个人中枢)                                │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Hermes File Manager                            │
│     团队文件管理 · 空间/成员/配额 · RBAC 权限 · 生命周期        │
│                       (团队协作层)                              │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓ /knowledge/sync
┌─────────────────────────────────────────────────────────────────┐
│                        LLM Wiki                                  │
│    知识编译（Ingest/Compile/Query/Lint）· 三层架构· 语义搜索      │
│                       (知识沉淀层)                               │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓ wiki 目录
┌─────────────────────────────────────────────────────────────────┐
│                  Obsidian + Claudian                             │
│           可视化浏览 · 图谱视图 · AI 内联编辑                    │
│                       (知识消费层)                              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 OpenHuman vs Hermes 准确差异

| 维度 | OpenHuman | Hermes 主系统 | Hermes File Manager |
|------|-----------|--------------|---------------------|
| **服务对象** | 个人用户 | 个人用户 | 团队 |
| **核心能力** | AI 助手 + auto-fetch | 消息路由 | 文件管理 + RBAC |
| **知识管理** | Memory Tree（浅） | ❌ 无 | LLM Wiki 同步（深） |
| **团队协作** | ❌ 无 | ❌ 无 | ✅ 完整 |
| **118+ 集成** | ✅ OAuth 一键 | ❌ 无 | ❌ 无 |
| **认证机制** | 本地账号 | 平台 Pairing | JWT 用户认证 |

### 2.3 关键问题

> **OpenHuman 的 Memory Tree 能否成为 Hermes 主系统的"前端感知层"？**

- OpenHuman 知道"你今天收到了什么邮件、开了什么会"
- Hermes 主系统知道"如何路由消息、处理任务"
- **整合后**：AI 能基于 OpenHuman 抓取的上下文，在 Hermes 里执行团队任务

---

## 三、知识共享路径设计

### 3.1 三种整合路径对比

| 路径 | 描述 | 优点 | 缺点 | 推荐度 |
|------|------|------|------|--------|
| **路径 A** | File Manager 作为知识共享入口 | 改动最小、复用现有 RBAC | LLM Wiki 需改造认证 | ⭐⭐⭐ |
| **路径 B** | 构建独立知识共享服务 | 独立可扩展 | 工作量大 | ⭐⭐ |
| **路径 C** | OpenHuman 团队化（团队 Memory Tree） | 深度整合 | OpenHuman 个人定位，需大改 | ⭐ |

### 3.2 路径 A：基于 File Manager 的渐进方案

**核心思路**：利用现有基础设施，File Manager 的空间/成员/配额直接复用，只需给 LLM Wiki 增加认证层。

**架构图**

```
团队成员（Web / Desktop）
       ↓ 登录 Hermes 账号 (JWT)
Hermes File Manager
       ↓ team_id + user_id 传入
LLM Wiki Engine（新增认证层）
       ↓ wiki 目录（团队隔离）
Obsidian Vault（团队共享 Vault）
       ↓ MCP
Claudian（团队成员直接操作知识库）
```

### 3.3 具体步骤

| 步骤 | 内容 | 优先级 | 状态 |
|------|------|--------|------|
| 1 | 给 LLM Wiki 增加 JWT 验证（信任 File Manager 传入的 token） | P0 | 待开发 |
| 2 | File Manager `/knowledge/sync` 支持团队空间隔离（team_id） | P0 | 待开发 |
| 3 | LLM Wiki wiki 目录按 team_id 隔离存储 | P0 | 待开发 |
| 4 | Obsidian 通过 URL/路径打开团队 wiki 目录作为 Vault | P1 | 待开发 |
| 5 | Claudian MCP 连接到 File Manager（知识共享） | P2 | 待开发 |
| 6 | 团队 Memory Tree（参考 OpenHuman auto-fetch） | P2 | 远期规划 |

---

## 四、知识库访问方式决策

### 4.1 访问方式选择

| 方式 | 说明 | 适用场景 |
|------|------|---------|
| **Web 界面** | 通过浏览器访问 File Manager 的知识视图 | 大多数团队成员 |
| **桌面应用** | Obsidian 打开团队 Vault | 需要深度编辑的成员 |
| **MCP 工具** | Claudian 通过 MCP 调用知识库 | 技术用户/AI 辅助 |
| **混合** | 以上都有，按需使用 | 完整方案 |

### 4.2 推荐：混合方式

| 用户类型 | 访问方式 |
|---------|---------|
| 普通成员 | Web 界面浏览 + 搜索 |
| 内容贡献者 | Obsidian 编辑 + Claudian AI 辅助 |
| 技术成员 | MCP 工具调用 |

---

## 五、账号统一是整合基础

### 5.1 为什么需要统一账号

当前各系统各自为政：
- OpenHuman：本地账号
- Hermes 主系统：平台 Pairing（Discord/Telegram 用户）
- Hermes File Manager：JWT 用户认证
- LLM Wiki：无认证

没有统一账号，就无法做到：
- 团队成员识别（谁在访问知识库）
- 权限控制（谁能编辑/谁能只读）
- 审计追溯（谁在什么时间访问了什么）

### 5.2 统一账号架构

```
用户（Email/Password 或 OAuth）
       ↓
Auth Service (JWT 签发)
       ↓
File Manager (RBAC 空间权限)
       ↓ team_id + user_id
LLM Wiki (知识库访问控制)
       ↓
团队 Wiki (Obsidian Vault)
```

---

## 六、技术实现要点

### 6.1 LLM Wiki 认证改造

```python
# 方案：在 LLM Wiki 的同步 API 中增加 JWT 验证
@app.post("/knowledge/sync")
async def sync_to_knowledge(
    request: Request,
    team_id: str,
    user_ctx = Depends(get_current_user_ctx)  # JWT 验证
):
    # 1. 验证 user_ctx 是否属于 team_id
    # 2. 获取该用户在团队中的角色（owner/member/viewer）
    # 3. 根据角色决定：只读 / 可写 / 可管理
    # 4. 调用 LLM Wiki 引擎时传入 user_id（用于隔离）
```

### 6.2 团队 wiki 隔离

```
LLM Wiki 存储结构：
  /storage/llm_wiki/
    ├── team_{team_id_1}/
    │   ├── wiki/
    │   ├── raw/
    │   └── outputs/
    ├── team_{team_id_2}/
    │   └── ...
```

### 6.3 Claude Code MCP 集成

```json
// Claudian MCP 配置示例
{
  "mcpServers": {
    "hermes-file-manager": {
      "command": "hermes",
      "args": ["mcp", "serve"],
      "env": {
        "API_BASE": "http://localhost:8080/api/v1"
      }
    }
  }
}
```

---

## 七、OpenHuman 的借鉴价值

### 7.1 可以借鉴的能力

| OpenHuman 特性 | 借鉴方向 |
|--------------|---------|
| auto-fetch | 团队数据自动抓取（Gmail 群组日历、Slack 频道） |
| Memory Tree | 团队级别的上下文记忆 |
| TokenJuice | 降低 API 成本（适用于 LLM Wiki 编译） |
| 模型路由 | 按任务自动选择 LLM（推理/快速/视觉） |

### 7.2 团队 Memory Tree 设计

```
个人 Memory Tree（OpenHuman）
       ↓ 团队化
团队 Memory Tree

内容：
- 团队决策历史（meeting notes 摘要）
- 成员角色和职责
- 项目进展快照
- 共享文档索引

特点：
- 跨成员共享（不是个人的）
- 定时 auto-sync（20 分钟）
- LLM Wiki 作为编译层
```

---

## 八、下一步行动

- [ ] 确认技术方案（路径 A / B / C）
- [ ] 确定知识库访问方式（Web / Desktop / MCP / 混合）
- [ ] 设计 LLM Wiki 认证层 API
- [ ] 实现团队 wiki 存储隔离
- [ ] 设计团队 Memory Tree

---

## 九、相关文档

- [08_统一账号](../08_统一账号/README.md) — 统一账号体系设计
- [LLM Wiki 详解](../08_统一账号/05_llmwiki_detail.md) — LLM Wiki 技术细节
- [Hermes 集成方案](../08_统一账号/03_hermes_integration.md) — Hermes 与生态集成