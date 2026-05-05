#!/bin/bash
#==============================================================================
# Hermes File Manager 构建脚本 (简化版)
# 统一构建流程：前端构建 + Tauri Release 打包 + 版本化
#
# 原则:
# - Tauri bundle.resources 自动嵌入 web/dist，无需手动复制
# - 窗口 URL 配置为 app.html (相对于 Resources/)
# - 构建产物版本化：包含 Cargo 版本 + 前端内容 Hash
#==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEB_DIR="$PROJECT_ROOT/web"
TAURI_DIR="$PROJECT_ROOT/src-tauri"
APP_NAME="Hermes File Manager"
APP_PATH="/Applications/$APP_NAME.app"
BACKUP_DIR="/tmp/hermes-backup"
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================================================
# 版本生成函数
# ============================================================================
generate_version_info() {
    local dist_dir="$1"
    local cargo_version="$2"

    # 计算前端内容的 SHA256 hash (只哈希关键文件)
    # 最终 hash = 所有文件 hash 的再 hash，确保内容变化时 hash 变化
    local content_hash=$(find "$dist_dir" -type f \( -name "*.html" -o -name "*.js" -o -name "*.css" \) \
        -exec shasum -a 256 {} \; 2>/dev/null | shasum -a 256 | awk '{print $1}' | shasum -a 256 | awk '{print $1}')

    # 短 hash 用于版本标识 (前8字符)
    local short_hash=$(echo "$content_hash" | cut -c1-8)

    # 构建版本标识
    local version_string="${cargo_version}+${short_hash}"

    # 输出 JSON 格式版本信息
    # macOS du 不支持 -b，使用 -s 代替
    local dist_size=$(du -s "$dist_dir" 2>/dev/null | awk '{print $1}')
    cat << EOF
{
    "cargo_version": "${cargo_version}",
    "content_hash": "${content_hash}",
    "short_hash": "${short_hash}",
    "version_string": "${version_string}",
    "build_timestamp": "${TIMESTAMP}",
    "dist_size": ${dist_size}
}
EOF
}

echo "============================================"
echo "Hermes File Manager 构建脚本"
echo "============================================"

# ============================================================================
# 步骤 1: 预检查
# ============================================================================
echo ""
log_info "[1/7] 预检查..."

# 获取 Cargo.toml 中的版本
CARGO_VERSION=$(grep "version" src-tauri/Cargo.toml | head -1 | cut -d"\"" -f2)
if [ -z "$CARGO_VERSION" ]; then
    CARGO_VERSION="0.0.0"
fi
log_info "Cargo 版本: ${CARGO_VERSION}"

if [ ! -d "$WEB_DIR/dist" ]; then
    log_warn "前端构建产物不存在，将重新构建"
else
    SIZE=$(stat -f%z "$WEB_DIR/dist/vue.html" 2>/dev/null || stat -c%s "$WEB_DIR/dist/vue.html" 2>/dev/null)
    log_info "前端构建产物已存在: ${SIZE} bytes"
fi

# ============================================================================
# 步骤 2: 生成版本信息
# ============================================================================
echo ""
log_info "[2/7] 生成版本信息..."

if [ -d "$WEB_DIR/dist" ]; then
    VERSION_JSON=$(generate_version_info "$WEB_DIR/dist" "$CARGO_VERSION")
    VERSION_STRING=$(echo "$VERSION_JSON" | grep -o '"version_string"[^,]*' | cut -d'"' -f4)
    SHORT_HASH=$(echo "$VERSION_JSON" | grep -o '"short_hash"[^,]*' | cut -d'"' -f4)
    CONTENT_HASH=$(echo "$VERSION_JSON" | grep -o '"content_hash"[^,]*' | cut -d'"' -f4)

    log_info "内容 Hash: ${CONTENT_HASH}"
    log_info "版本标识: ${VERSION_STRING}"

    # 保存版本信息供后续使用
    echo "$VERSION_JSON" > "$WEB_DIR/dist/VERSION.json"
else
    VERSION_STRING="${CARGO_VERSION}+pending"
    SHORT_HASH="pending"
fi

# ============================================================================
# 步骤 3: 备份
# ============================================================================
echo ""
log_info "[3/7] 备份当前版本..."

mkdir -p "$BACKUP_DIR"
if [ -d "$APP_PATH" ]; then
    # 使用版本化的备份名称
    BACKUP_PATH="$BACKUP_DIR/${APP_NAME}-${VERSION_STRING}-${TIMESTAMP}.app"
    cp -r "$APP_PATH" "$BACKUP_PATH"
    log_info "已备份: $BACKUP_PATH"
fi

# ============================================================================
# 步骤 4: 停止应用
# ============================================================================
echo ""
log_info "[4/7] 停止运行中的应用..."
pkill -f "$APP_NAME" 2>/dev/null || true
sleep 1

# ============================================================================
# 步骤 5: 构建前端
# ============================================================================
echo ""
log_info "[5/7] 构建前端..."
cd "$WEB_DIR"
rm -rf dist
NODE_ENV=production npm run build

if [ ! -f "dist/app.html" ]; then
    log_error "前端构建失败"
    exit 1
fi

# 复制 js/ 目录到 dist（lifecycle-interceptor.js 等独立模块）
if [ -d "js" ]; then
    cp -r js dist/
    log_info "已复制 js/ 目录到 dist/"
fi

# 重新生成版本信息（确保使用最新构建）
if [ -d "$WEB_DIR/dist" ]; then
    VERSION_JSON=$(generate_version_info "$WEB_DIR/dist" "$CARGO_VERSION")
    VERSION_STRING=$(echo "$VERSION_JSON" | grep -o '"version_string"[^,]*' | cut -d'"' -f4)
    SHORT_HASH=$(echo "$VERSION_JSON" | grep -o '"short_hash"[^,]*' | cut -d'"' -f4)
    CONTENT_HASH=$(echo "$VERSION_JSON" | grep -o '"content_hash"[^,]*' | cut -d'"' -f4)

    echo "$VERSION_JSON" > "$WEB_DIR/dist/VERSION.json"
fi

SIZE=$(stat -f%z "dist/vue.html" 2>/dev/null || stat -c%s "dist/vue.html" 2>/dev/null)
log_info "前端构建完成: vue.html (${SIZE} bytes)"
log_info "版本标识: ${VERSION_STRING}"

# ============================================================================
# 步骤 6: 构建 Tauri
# ============================================================================
echo ""
log_info "[6/7] 构建 Tauri Release..."
cd "$TAURI_DIR"

if ! cargo tauri build 2>&1; then
    log_error "Tauri 构建失败"
    [ -d "$BACKUP_PATH" ] && cp -r "$BACKUP_PATH" "$APP_PATH"
    exit 1
fi

# ============================================================================
# 步骤 7: 验证 Bundle
# ============================================================================
echo ""
log_info "[7/7] 验证 Bundle..."

BUNDLE_APP="$TAURI_DIR/target/release/bundle/macos/$APP_NAME.app"

# 验证 vue.html（resources 配置直接展开到 Resources/ 根目录）
EXPECTED_PATH="$BUNDLE_APP/Contents/Resources/vue.html"
VERSION_PATH="$BUNDLE_APP/Contents/Resources/VERSION.json"

if [ -f "$EXPECTED_PATH" ]; then
    BUNDLE_SIZE=$(stat -f%z "$EXPECTED_PATH" 2>/dev/null || stat -c%s "$EXPECTED_PATH" 2>/dev/null)
    log_info "Bundle 验证通过: vue.html (${BUNDLE_SIZE} bytes)"
else
    log_error "Bundle 验证失败: 缺少 $EXPECTED_PATH"
    ls -laR "$BUNDLE_APP/Contents/Resources/" 2>/dev/null || true
    log_warn "触发回滚机制: 恢复到上一个正常工作版本"
    [ -d "$BACKUP_PATH" ] && cp -r "$BACKUP_PATH" "$APP_PATH" && log_info "回滚完成"
    exit 1
fi

# 验证 VERSION.json 是否在 bundle 中
if [ -f "$VERSION_PATH" ]; then
    log_info "版本信息已嵌入: VERSION.json"
    cat "$VERSION_PATH"
else
    log_warn "VERSION.json 未找到（首次构建正常）"
fi

# 安装 (使用 rsync 确保正确复制所有文件)
rm -rf "$APP_PATH"
rsync -av "$BUNDLE_APP/" "$APP_PATH/"

echo ""
echo "============================================"
echo "构建完成!"
echo "============================================"
echo "前端: $WEB_DIR/dist/"
echo "版本: ${VERSION_STRING}"
echo "Hash: ${CONTENT_HASH}"
echo "安装: $APP_PATH"
echo ""
echo "启动应用..."
open -a "$APP_NAME"

# 清理 7 天前备份
find "$BACKUP_DIR" -type d -name "*.app" -mtime +7 -exec rm -rf {} \; 2>/dev/null || true