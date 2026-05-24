# Hermes Agent 跨机器迁移指南

## 概述

本文档描述如何将 Hermes Agent 完整系统从一台 Mac 迁移到另一台 Mac。

---

## 流程概览

```
┌─────────────────┐     导出      ┌─────────────────┐
│   旧 Mac        │ ────────── → │   文件          │
│   (当前机器)    │              │   hermes_migration_*.tar.gz │
└─────────────────┘              └─────────────────┘
                                        │
                                        ▼
                                   ┌─────────────────┐
        恢复      ┌──────────────── │   新 Mac        │
         ← ───── │                 │   (目标机器)     │
                 └─────────────────└─────────────────┘
```

---

## 第一阶段：旧机器导出

### 1.1 运行导出脚本

```bash
cd ~/hermes-agent
chmod +x scripts/migration/export_hermes_data.sh
./scripts/migration/export_hermes_data.sh
```

### 1.2 导出内容包括

| 内容 | 说明 | 重要性 |
|------|------|--------|
| `env_config.env` | 环境变量配置（无敏感信息） | ⚠️ 需手动补充密钥 |
| `hermes_config/` | `~/.hermes/` 全部配置 | ✅ 必须 |
| `claude_config/` | `~/.claude/` 配置和记忆 | ✅ 推荐 |
| `databases/*.db` | SQLite 数据库文件 | ✅ 推荐 |
| `obsidian_config/` | Claudian 插件配置 | ⚠️ 如使用 Obsidian |
| `restore_hermes.sh` | 自动恢复脚本 | ✅ 必须 |

### 1.3 复制到新机器

方式一：U盘/硬盘
```bash
cp hermes_migration_20260524.tar.gz /Volumes/你的U盘/
```

方式二：网络传输
```bash
# 如果两台机器在同一网络
scp hermes_migration_20260524.tar.gz user@新机器IP:~/
```

---

## 第二阶段：新机器部署

### 2.1 预检查

确保新机器满足：
- macOS 12.0+
- Xcode Command Line Tools: `xcode-select --install`

### 2.2 运行部署脚本

```bash
# 1. 解压
cd ~
tar -xzf hermes_migration_*.tar.gz

# 2. 运行部署脚本
chmod +x deploy_hermes.sh
./deploy_hermes.sh
```

### 2.3 或者手动部署

如果部署脚本有问题，可以手动：

```bash
# 1. 安装依赖
brew install rust node@18 python@3.11

# 2. 克隆项目
git clone https://github.com/your-repo/hermes-agent.git ~/hermes-agent
cd ~/hermes-agent
git checkout main

# 3. 恢复配置
cd migration_export_*
./restore_hermes.sh

# 4. 安装 Python 依赖
cd ~/hermes-agent
python3 -m venv venv
source venv/bin/activate
pip install -e .

# 5. 安装 Node 依赖
cd tools/file_manager/web && npm install && cd -
cd tools/claudian_hermes_plugin && npm install && cd -

# 6. 编译 LLM Wiki
cd tools/llm_wiki_FM && cargo build --release && cd -
```

---

## 第三阶段：验证

### 3.1 服务验证

```bash
# 检查 Hermes File Manager
curl http://localhost:8080/health

# 检查 LLM Wiki
curl http://localhost:19827/health

# 检查 MCP Server
cd tools/claudian_hermes_plugin && npm run build
```

### 3.2 功能验证

| 功能 | 测试方法 |
|------|---------|
| Web UI | 浏览器打开 http://localhost:8080 |
| 用户登录 | 尝试登录 |
| 文件上传 | 上传一个测试文件 |
| LLM Wiki | 打开 LLM Wiki.app |
| MCP 工具 | 在 Claude Code 中运行 `@hermes list-spaces` |

---

## 第四阶段：数据迁移（可选）

### 4.1 如果需要迁移历史数据

在旧机器上：
```bash
# 导出数据库
cp ~/.hermes/file_manager/*.db ./migration_databases/
```

在新机器上恢复后：
```bash
# 替换数据库文件
cp ./migration_databases/*.db ~/.hermes/file_manager/
```

### 4.2 LLM Wiki 数据

```bash
# 导出
cp -r ~/.hermes/llm_wiki ./migration_llm_wiki/

# 恢复
cp -r ./migration_llm_wiki/* ~/.hermes/llm_wiki/
```

---

## 注意事项

### 环境变量

`.env` 文件中的敏感信息（密码、API密钥）不会导出，需要在新机器上手动配置：

```bash
# 创建新的 .env 文件
cp .env.example .env
nano .env  # 填入实际密钥
```

### 端口冲突

如果 8080、19827、1421 端口被占用：

```bash
# 查看占用端口的进程
lsof -i :8080

# 终止进程
kill -9 <PID>
```

### Intel Mac

Intel Mac 兼容性很好，大部分预编译二进制可直接使用：

```bash
# 确认是 Intel 架构
uname -m  # 应输出 x86_64

# 如果之前在其他机器上使用过，建议清理后重新编译
cd tools/llm_wiki_FM
rm -rf target
cargo build --release
```

### Apple Silicon（如果未来迁移）

未来如果迁移到 Apple Silicon：

```bash
# 需要重新编译
cd tools/llm_wiki_FM
cargo clean
cargo build --release

# 或安装 Rosetta 转译兼容
```

---

## 故障排除

### 问题：Python 找不到模块

```bash
source venv/bin/activate
pip install -e .
```

### 问题：Node 模块安装失败

```bash
cd tools/file_manager/web
rm -rf node_modules package-lock.json
npm install
```

### 问题：LLM Wiki 编译失败

```bash
cd tools/llm_wiki_FM
rm -rf target
cargo build --release 2>&1 | tail -50
```

---

## 快速参考

### 启动服务
```bash
./start_services.sh
```

### 停止服务
```bash
./stop_services.sh
```

### 查看日志
```bash
tail -f ~/.hermes/file_manager/logs/*.log
```

### 重新初始化
```bash
rm -rf ~/.hermes
./restore_hermes.sh
./start_services.sh
```