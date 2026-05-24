#!/bin/bash
# Hermes Agent 数据迁移导出脚本
# 用法: ./scripts/migration/export_hermes_data.sh

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

LOG_FILE="hermes_migration_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[✓] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[!] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[✗] $1${NC}" | tee -a "$LOG_FILE"
}

# 检查是否在正确的目录
if [ ! -d ".git" ]; then
    error "请在 hermes-agent 项目根目录运行此脚本"
    exit 1
fi

log "开始 Hermes Agent 数据导出..."
log "日志文件: $LOG_FILE"

# 创建导出目录
EXPORT_DIR="./migration_export_$(date +%Y%m%d)"
mkdir -p "$EXPORT_DIR"
cd "$EXPORT_DIR"

# 1. 导出环境变量
log "📦 导出环境变量..."
if [ -f "../.env" ]; then
    # 移除敏感信息（密码、密钥）但保留其他配置
    grep -v "PASSWORD\|SECRET\|KEY\|TOKEN" ../.env > env_config.env 2>/dev/null || true
    success "环境变量已导出到 env_config.env（敏感信息已排除）"
else
    warn "未找到 .env 文件，跳过"
fi

# 2. 导出 Hermes 配置目录
log "📦 导出 Hermes 配置..."
if [ -d "$HOME/.hermes" ]; then
    cp -r "$HOME/.hermes" ./hermes_config
    success "Hermes 配置已导出到 hermes_config/"
else
    warn "未找到 ~/.hermes 目录，跳过"
fi

# 3. 导出 Claude 配置
log "📦 导出 Claude 配置..."
if [ -d "$HOME/.claude" ]; then
    # 排除缓存和临时文件
    rsync -av --exclude='*.log' --exclude='__pycache__' --exclude='.cache' \
        "$HOME/.claude/" ./claude_config/ 2>/dev/null || \
        cp -r "$HOME/.claude" ./claude_config 2>/dev/null || true
    success "Claude 配置已导出到 claude_config/"
else
    warn "未找到 ~/.claude 目录，跳过"
fi

# 4. 导出数据库
log "📦 导出数据库..."
if [ -d "$HOME/.hermes/file_manager" ]; then
    mkdir -p databases
    # 复制 SQLite 数据库
    find "$HOME/.hermes/file_manager" -name "*.db" -exec cp {} ./databases/ \;
    # 复制 LLM Wiki 数据库
    if [ -d "$HOME/.hermes/llm_wiki" ]; then
        find "$HOME/.hermes/llm_wiki" -name "*.db" -exec cp {} ./databases/ \;
    fi
    success "数据库已导出到 databases/"
else
    warn "未找到数据库文件，跳过"
fi

# 5. 导出 Obsidian Vault 配置（如果存在）
log "📦 导出 Obsidian 配置..."
OBSIDIAN_PLUGINS="$HOME/.obsidian/plugins"
if [ -d "$OBSIDIAN_PLUGINS" ]; then
    mkdir -p obsidian_config
    # 只导出 Claudian 相关配置
    if [ -d "$OBSIDIAN_PLUGINS/claudian" ]; then
        cp -r "$OBSIDIAN_PLUGINS/claudian" ./obsidian_config/
    fi
    if [ -d "$OBSIDIAN_PLUGINS/hermes-mcp" ]; then
        cp -r "$OBSIDIAN_PLUGINS/hermes-mcp" ./obsidian_config/
    fi
    success "Obsidian 配置已导出到 obsidian_config/"
else
    warn "未找到 Obsidian 配置，跳过"
fi

# 6. 导出项目配置
log "📦 导出项目配置..."
if [ -f "../config.yaml" ]; then
    cp ../config.yaml ./project_config.yaml
    success "项目配置已导出"
fi

# 7. 创建恢复脚本
log "📦 生成恢复脚本..."
cat > restore_hermes.sh << 'RESTORE_EOF'
#!/bin/bash
# Hermes Agent 数据恢复脚本
# 用法: ./restore_hermes.sh

set -e

EXPORT_DIR=$(dirname "$0")

echo "开始恢复 Hermes Agent 配置..."

# 恢复 Hermes 配置
if [ -d "$EXPORT_DIR/hermes_config" ]; then
    cp -r "$EXPORT_DIR/hermes_config/"* "$HOME/.hermes/"
    echo "✓ Hermes 配置已恢复"
fi

# 恢复 Claude 配置
if [ -d "$EXPORT_DIR/claude_config" ]; then
    cp -r "$EXPORT_DIR/claude_config/"* "$HOME/.claude/"
    echo "✓ Claude 配置已恢复"
fi

# 恢复数据库
if [ -d "$EXPORT_DIR/databases" ]; then
    mkdir -p "$HOME/.hermes/file_manager"
    mkdir -p "$HOME/.hermes/llm_wiki"
    cp "$EXPORT_DIR/databases/"* "$HOME/.hermes/file_manager/"
    echo "✓ 数据库已恢复"
fi

# 恢复 Obsidian 配置
if [ -d "$EXPORT_DIR/obsidian_config" ]; then
    mkdir -p "$HOME/.obsidian/plugins"
    cp -r "$EXPORT_DIR/obsidian_config/"* "$HOME/.obsidian/plugins/"
    echo "✓ Obsidian 配置已恢复"
fi

echo "恢复完成！请重新启动服务。"
RESTORE_EOF
chmod +x restore_hermes.sh
success "恢复脚本已生成: restore_hermes.sh"

# 8. 创建部署检查清单
log "📦 生成部署检查清单..."
cat > DEPLOYMENT_CHECKLIST.md << 'CHECKLIST_EOF'
# Hermes Agent 部署检查清单

## 前提条件

- [ ] macOS 12.0+
- [ ] Xcode Command Line Tools: `xcode-select --install`
- [ ] Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- [ ] Git

## 安装步骤

### 1. 安装基础依赖

```bash
# 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 安装 Node.js 18
brew install node@18

# 安装 Python 3.11
brew install python@3.11
```

### 2. 克隆项目

```bash
git clone <your-repo-url> ~/hermes-agent
cd ~/hermes-agent
git checkout main
```

### 3. 运行恢复脚本

```bash
cd migration_export_<date>
./restore_hermes.sh
```

### 4. 安装依赖

```bash
# 安装 Python 依赖
cd ~/hermes-agent
pip install -e .

# 安装 Node 依赖
cd tools/file_manager/web
npm install

cd ../claudian_hermes_plugin
npm install
```

### 5. 编译 LLM Wiki

```bash
cd tools/llm_wiki_FM
cargo build --release
```

### 6. 验证安装

```bash
# 启动 Hermes File Manager
cd tools/file_manager
python server.py &

# 验证服务
curl http://localhost:8080/health
curl http://localhost:19827/health

# 编译 TypeScript
cd tools/claudian_hermes_plugin
npm run build
```

## 端口占用检查

如果端口被占用，使用以下命令查找：

```bash
# 查找占用端口的进程
lsof -i :8080
lsof -i :19827
lsof -i :1421

# 终止进程
kill -9 <PID>
```

## 常见问题

### Rust 编译错误

```bash
# 清理 Rust 缓存
cargo clean
rm -rf target
cargo build --release
```

### Python 包安装失败

```bash
# 使用虚拟环境
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Node 模块安装错误

```bash
rm -rf node_modules package-lock.json
npm install
```
CHECKLIST_EOF
success "部署检查清单已生成: DEPLOYMENT_CHECKLIST.md"

# 9. 打包导出
log "📦 打包导出文件..."
tar -czf "hermes_migration_$(date +%Y%m%d).tar.gz" \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='.git' \
    .
success "导出完成: hermes_migration_$(date +%Y%m%d).tar.gz"

# 回到原目录
cd ..

log ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success "导出完成！"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "导出目录: $EXPORT_DIR"
log "打包文件: hermes_migration_$(date +%Y%m%d).tar.gz"
log ""
log "在新机器上："
log "1. 解压: tar -xzf hermes_migration_*.tar.gz"
log "2. 运行: cd migration_export_* && ./restore_hermes.sh"
log "3. 按照 DEPLOYMENT_CHECKLIST.md 完成部署"
log ""