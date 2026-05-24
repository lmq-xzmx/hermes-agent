# IT 预装验证 Checklist

> **创建日期**: 2026-05-24
> **用途**: IT 部门在员工入职前执行预装验证
> **预计耗时**: 15 分钟/台

---

## 一、预装清单

### 1.1 软件安装

| 项目 | 验证方法 | 状态 |
|------|---------|------|
| Obsidian 已安装 | 双击图标能打开 | ☐ |
| Claudian 插件已安装 | Obsidian 设置 → 第三方插件中可见 Claudian | ☐ |
| hermes-mcp 系统服务已注册 | Windows 服务列表或 macOS launchd 中可见 | ☐ |

### 1.2 Claudian 企业配置

配置文件位置：`.obsidian/plugins/claudian/config.json`

```json
{
  "enterprise_mode": true,
  "default_share_mode": "full_share",
  "mcp_server": {
    "type": "system_service",
    "auto_start": true
  },
  "auth": {
    "method": "sso_auto",
    "token_refresh": "auto"
  },
  "sync": {
    "mode": "auto_incremental",
    "on_save": true
  },
  "notifications": {
    "show_welcome": true,
    "show_tips": true
  }
}
```

**验证步骤**：
1. 打开配置文件确认上述配置存在
2. 验证 `enterprise_mode: true`
3. 验证 `sync.on_save: true`

### 1.3 SSO 自动签发 JWT

| 验证项 | 操作 | 预期结果 |
|--------|------|----------|
| 首次启动自动获取 Token | 打开 Obsidian，观察 Claudian 日志 | 显示「JWT Token 已获取」 |
| Token 自动刷新 | 检查 Token 剩余有效期 | > 30 分钟 |

### 1.4 hermes-mcp 连接

```bash
# 验证 hermes-mcp 服务状态
# Windows
sc query HermesMCP

# macOS
launchctl list | grep hermes

# 验证 MCP 连接
# 在 Obsidian 中打开命令面板 Ctrl+P
# 输入 @hermes list-spaces
# 应显示可用的 Space 列表
```

---

## 二、端到端验证

### 2.1 测试账号

使用 IT 测试账号（非员工真实账号）：

| 字段 | 值 |
|------|-----|
| 部门 | IT-Test-Department |
| 角色 | editor |
| Space | hermes-test |

### 2.2 验证流程

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 打开 Obsidian | 显示欢迎引导动画（首次启动） |
| 2 | 创建一篇测试笔记 | 右下角显示「✅ 已同步到团队知识库」 |
| 3 | 打开命令面板 `@hermes search-wiki` | 显示搜索界面 |
| 4 | 搜索测试笔记标题 | 能搜索到刚创建的笔记 |
| 5 | 打开设置 → 知识库共享 | 显示「已连接到团队 hermes-test」 |

### 2.3 验证日志

完成后在 Claudian 日志中确认：

```
[INFO] Enterprise mode: enabled
[INFO] Default share mode: full_share
[INFO] SSO auto token: success
[INFO] MCP server connected: hermes-mcp
[INFO] Sync on save: enabled
[INFO] Auto sync initialized
```

---

## 三、常见问题

| 问题 | 可能原因 | 解决步骤 |
|------|---------|----------|
| hermes-mcp 未运行 | 服务未安装/未启动 | 重新安装 hermes-mcp 服务 |
| JWT Token 获取失败 | SSO 配置错误 | 检查 `config.json` 中的 SSO 配置 |
| 同步失败 | 网络问题/权限问题 | 检查网络连接和 Space 权限 |
| Claudian 插件未显示 | 插件未正确安装 | 重新安装 Claudian 插件 |

---

## 四、完成确认

完成上述验证后，在下方签字确认：

| IT 工程师 | 日期 | 签名 |
|-----------|------|------|
| | | |

**验证通过后**，员工电脑可交付使用。

---

## 五、相关文档

- [完全共享模式开发计划](./10_完全共享模式开发计划.md)
- [员工入职引导](./onboarding-checklist.md)
- [HR Webhook 接口规范](./hr-webhook-spec.md)