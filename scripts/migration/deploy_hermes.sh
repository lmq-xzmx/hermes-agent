#!/bin/bash
# Hermes Agent 自动化部署脚本
# 用法: ./scripts/migration/deploy_hermes.sh

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

# 检查是否为 macOS
if [[ "$(uname)" != "Darwin" ]]; then
    error "此脚本仅支持 macOS"
    exit 1
fi

log "开始部署 Hermes Agent..."

# ============================================================================
# 1. 检查 Xcode Command Line Tools
# ============================================================================
log "检查 Xcode Command Line Tools..."
if ! xcode-select -p &> /dev/null; then
    warn "Xcode Command Line Tools 未安装，正在安装..."
    xcode-select --install
    log "请在弹出的对话框中同意安装，然后重新运行此脚本"
    exit 1
fi
success "Xcode Command Line Tools 已安装"

# ============================================================================
# 2. 安装 Homebrew（如果需要）
# ============================================================================
log "检查 Homebrew..."
if ! command -v brew &> /dev/null; then
    warn "Homebrew 未安装，正在安装..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
success "Homebrew 已安装"

# ============================================================================
# 3. 安装基础依赖
# ============================================================================
log "安装基础依赖..."

# Rust
if ! command -v rustc &> /dev/null; then
    log "安装 Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
fi
success "Rust 已安装"

# Node.js 18
if ! command -v node &> /dev/null || [[ "$(node -v)" < "v18" ]]; then
    log "安装 Node.js 18..."
    brew install node@18
    export PATH="/usr/local/opt/node@18/bin:$PATH"
fi
success "Node.js $(node -v) 已安装"

# Python 3.11
if ! command -v python3 &> /dev/null || [[ "$(python3 --version)" != *"3.11"* ]]; then
    log "安装 Python 3.11..."
    brew install python@3.11
fi
export PATH="/usr/local/opt/python@3.11/bin:$PATH"
success "Python $(python3 --version) 已安装"

# ============================================================================
# 4. 克隆或更新项目
# ============================================================================
log "准备项目目录..."

if [ -d "$HOME/hermes-agent" ]; then
    cd "$HOME/hermes-agent"
    log "更新现有项目..."
    git pull origin main
else
    log "克隆项目（请替换为你的仓库 URL）..."
    # TODO: 替换为实际仓库 URL
    # git clone https://github.com/your-repo/hermes-agent.git "$HOME/hermes-agent"
    warn "请手动克隆项目或配置仓库 URL"
fi

cd "$HOME/hermes-agent"

# ============================================================================
# 5. 安装 Python 依赖
# ============================================================================
log "安装 Python 依赖..."
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -e .

# 安装项目依赖
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
success "Python 依赖安装完成"

# ============================================================================
# 6. 安装 Node 依赖
# ============================================================================
log "安装 Node 依赖..."

cd tools/file_manager/web
npm install
cd -

cd tools/claudian_hermes_plugin
npm install
npm run build
cd -

success "Node 依赖安装完成"

# ============================================================================
# 7. 编译 LLM Wiki（Intel Mac 优化）
# ============================================================================
log "编译 LLM Wiki（这可能需要几分钟）..."

cd tools/llm_wiki_FM

# Intel Mac 通常有更好的并行编译支持
cpu_cores=$(sysctl -n hw.ncpu 2>/dev/null || echo 4)
log "使用 $cpu_cores 核心并行编译..."

# 清理旧构建
cargo clean 2>/dev/null || true

# 并行编译
CARGO_BUILD_JOBS=$cpu_cores cargo build --release 2>&1 | tail -10

cd -

success "LLM Wiki 编译完成"

# ============================================================================
# 8. 恢复配置（如有）
# ============================================================================
if [ -f "$HOME/migration_export_*/restore_hermes.sh" ]; then
    log "发现迁移数据，正在恢复..."
    # 找到最新的导出目录
    MIGRATION_DIR=$(ls -dt $HOME/migration_export_* 2>/dev/null | head -1)
    if [ -n "$MIGRATION_DIR" ]; then
        cd "$MIGRATION_DIR"
        ./restore_hermes.sh
        cd "$HOME/hermes-agent"
    fi
fi

# ============================================================================
# 9. 验证安装
# ============================================================================
log "验证安装..."

# 检查端口
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t &> /dev/null; then
        warn "端口 $port 已被占用"
        return 1
    fi
    return 0
}

check_port 8080 || true
check_port 19827 || true

# 启动服务测试
log "启动 Hermes File Manager..."
cd tools/file_manager
python3 server.py &
SERVER_PID=$!
cd -

sleep 3

# 验证健康状态
if curl -s http://localhost:8080/health &> /dev/null; then
    success "Hermes File Manager 运行正常"
else
    warn "Hermes File Manager 启动可能有问题，请手动检查"
fi

# ============================================================================
# 10. 生成启动脚本
# ============================================================================
log "生成启动脚本..."

cat > "$HOME/hermes-agent/start_services.sh" << 'START_EOF'
#!/bin/bash
# Hermes Agent 服务启动脚本

echo "启动 Hermes Agent 服务..."

# 激活虚拟环境
cd "$(dirname "$0")"
source venv/bin/activate

# 启动 File Manager
cd tools/file_manager
python3 server.py &
FM_PID=$!

# 启动 LLM Wiki（如果已编译）
if [ -f "src-tauri/target/release/llm-wiki-fm" ]; then
    open -a "src-tauri/target/release/bundle/macos/LLM Wiki FM.app" 2>/dev/null || \
    ./src-tauri/target/release/llm-wiki-fm &
fi

echo "服务已启动 (PID: $FM_PID)"
echo "File Manager: http://localhost:8080"
echo "LLM Wiki: http://localhost:19827"
START_EOF
chmod +x "$HOME/hermes-agent/start_services.sh"

cat > "$HOME/hermes-agent/stop_services.sh" << 'STOP_EOF'
#!/bin/bash
# Hermes Agent 服务停止脚本

echo "停止 Hermes Agent 服务..."

# 查找并终止进程
pkill -f "python3 server.py" || true
pkill -f "llm-wiki-fm" || true
pkill -f "hermes-mcp" || true

echo "服务已停止"
STOP_EOF
chmod +x "$HOME/hermes-agent/stop_services.sh"

# ============================================================================
# 完成
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success "部署完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "启动服务: ./start_services.sh"
echo "停止服务: ./stop_services.sh"
echo ""
echo "Web UI: http://localhost:8080"
echo "API: http://localhost:8080/api/v1"
echo "LLM Wiki: http://localhost:19827"
echo ""
echo "详细文档请参考: DEPLOYMENT_CHECKLIST.md"
echo ""