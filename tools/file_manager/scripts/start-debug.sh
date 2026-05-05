#!/bin/bash
#==============================================================================
# 启动 Debug 版本
# Debug 和 Release 使用相同的前端构建产物，区别只是调试信息
#
# Rust 代码自动根据 debug_assertions 设置版本标签 [RELEASE]/[DEBUG]
# 不需要手动修改配置
#==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEB_DIR="$PROJECT_ROOT/web"
TAURI_DIR="$PROJECT_ROOT/src-tauri"
APP_NAME="Hermes File Manager"
DEBUG_APP="$TAURI_DIR/target/debug/bundle/macos/$APP_NAME.app"
DEBUG_RESOURCES="$DEBUG_APP/Contents/Resources"
BACKUP_DIR="/tmp/hermes-debug-backup"
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "============================================"
echo "Hermes File Manager - Debug 构建"
echo "============================================"

# ============================================================================
# 步骤 1: 停止运行中的应用
# ============================================================================
echo ""
log_info "[1/6] 停止运行中的应用..."
pkill -f "$APP_NAME" 2>/dev/null || true
sleep 1

# ============================================================================
# 步骤 2: 备份当前 Debug 版本（用于回滚）
# ============================================================================
echo ""
log_info "[2/6] 备份当前 Debug 版本..."
mkdir -p "$BACKUP_DIR"
if [ -d "$DEBUG_APP" ]; then
    BACKUP_PATH="$BACKUP_DIR/${APP_NAME}-DEBUG-${TIMESTAMP}.app"
    cp -r "$DEBUG_APP" "$BACKUP_PATH"
    log_info "已备份: $BACKUP_PATH"
else
    log_info "无现有 Debug 版本需要备份"
fi

# ============================================================================
# 步骤 3: 确保前端构建产物存在
# ============================================================================
echo ""
log_info "[3/6] 检查前端构建产物..."
cd "$WEB_DIR"
if [ ! -d "dist" ] || [ ! -f "dist/app.html" ]; then
    log_warn "前端构建产物不存在，重新构建..."
    npm run build
    cp floating.html dist/
else
    SIZE=$(stat -f%z "$WEB_DIR/dist/app.html" 2>/dev/null || stat -c%s "$WEB_DIR/dist/app.html" 2>/dev/null)
    log_info "前端构建产物已存在: app.html (${SIZE} bytes)"
fi

# ============================================================================
# 步骤 4: 构建 Debug 版本
# ============================================================================
echo ""
log_info "[4/6] 构建 Debug 版本..."
cd "$TAURI_DIR"
if ! cargo tauri build --debug 2>&1; then
    log_error "Debug 构建失败，尝试回滚..."
    if [ -d "$BACKUP_PATH" ]; then
        rm -rf "$DEBUG_APP"
        cp -r "$BACKUP_PATH" "$DEBUG_APP"
        log_info "已回滚到备份版本"
    fi
    exit 1
fi

# ============================================================================
# 步骤 5: 复制前端文件到 Debug bundle
# 路径必须与 tauri.conf.json 中的 window url 一致: ../Resources/_up_/web/dist/
# ============================================================================
echo ""
log_info "[5/6] 复制前端文件到 Debug bundle..."

# 清理旧的 resources 内容（避免旧文件）
rm -rf "$DEBUG_RESOURCES/_up_" 2>/dev/null || true

# 创建与 tauri.conf.json window url 对应的目录结构
mkdir -p "$DEBUG_RESOURCES/_up_/web/dist"
cp -r "$WEB_DIR/dist/"* "$DEBUG_RESOURCES/_up_/web/dist/"

if [ -f "$DEBUG_RESOURCES/_up_/web/dist/app.html" ]; then
    BUNDLE_SIZE=$(stat -f%z "$DEBUG_RESOURCES/_up_/web/dist/app.html" 2>/dev/null || stat -c%s "$DEBUG_RESOURCES/_up_/web/dist/app.html" 2>/dev/null)
    log_info "Bundle 文件复制成功: _up_/web/dist/app.html (${BUNDLE_SIZE} bytes)"
else
    log_error "Bundle 文件复制失败"
    exit 1
fi

echo "Debug Resources 内容:"
ls -laR "$DEBUG_RESOURCES/"

# ============================================================================
# 步骤 6: 启动 Debug 版本
# ============================================================================
echo ""
log_info "[6/6] 启动 Debug 版本..."
echo ""
echo "注意: Rust 代码会自动设置窗口标题为 'Hermes File Manager [DEBUG]'"
echo ""

"$DEBUG_APP/Contents/MacOS/hermes-file-manager"

# 清理超过 7 天的备份
find "$BACKUP_DIR" -type d -name "*.app" -mtime +7 -exec rm -rf {} \; 2>/dev/null || true