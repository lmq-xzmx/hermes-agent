#!/bin/bash
#==============================================================================
# Bundle 自动验证脚本 (TASK-005)
# 验证构建产物的正确性和完整性
#
# 验证项目:
# 1. Rust 代码行数 ≤ 200 (G1 目标)
# 2. 前端构建产物完整 (G3 SSOT)
# 3. Bundle 结构正确 (G6 资源嵌入)
# 4. CSP 配置安全 (HIST-015)
# 5. 窗口 URL 配置正确 (G8)
#==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEB_DIR="$PROJECT_ROOT/web"
TAURI_DIR="$PROJECT_ROOT/src-tauri"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASS++)) || true; }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; ((FAIL++)) || true; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo "============================================"
echo "Hermes File Manager - 构建自动验证"
echo "============================================"
echo ""

# ============================================================================
# 验证 1: Rust 代码行数 ≤ 200 (G1 目标)
# ============================================================================
echo "【验证 1/5】Rust 代码行数 (目标: ≤200)"

RUST_FILE="$TAURI_DIR/src/main.rs"
if [ -f "$RUST_FILE" ]; then
    RUST_LINES=$(wc -l < "$RUST_FILE" | tr -d ' ')
    if [ "$RUST_LINES" -le 200 ]; then
        log_pass "Rust 代码: ${RUST_LINES} 行 (≤200)"
    else
        log_fail "Rust 代码: ${RUST_LINES} 行 (超过 200 行限制)"
    fi
else
    log_fail "Rust 文件不存在: $RUST_FILE"
fi

echo ""

# ============================================================================
# 验证 2: 前端构建产物完整 (SSOT)
# ============================================================================
echo "【验证 2/5】前端构建产物 (SSOT)"

REQUIRED_FILES=(
    "dist/vue.html"
    "dist/assets/"
)

cd "$WEB_DIR"
for file in "${REQUIRED_FILES[@]}"; do
    if [ -e "$file" ]; then
        if [ -f "$file" ]; then
            SIZE=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
            log_pass "存在: $file (${SIZE} bytes)"
        else
            log_pass "存在: $file/ (目录)"
        fi
    else
        log_fail "缺失: $file"
    fi
done

# 验证 index.html 包含正确的基础路径
if [ -f "dist/index.html" ]; then
    if grep -q 'base href="/' "dist/index.html"; then
        log_pass "index.html 使用绝对路径 base href"
    elif grep -q 'base href="' "dist/index.html"; then
        BASE_HREF=$(grep -o 'base href="[^"]*"' "dist/index.html" | head -1)
        log_warn "index.html 使用相对路径: $BASE_HREF"
    fi
fi

echo ""

# ============================================================================
# 验证 3: Bundle 结构正确 (G6 资源嵌入)
# ============================================================================
echo "【验证 3/5】Bundle 结构 (G6 资源嵌入)"

RELEASE_BUNDLE="$TAURI_DIR/target/release/bundle/macos/Hermes File Manager.app"
DEBUG_BUNDLE="$TAURI_DIR/target/debug/bundle/macos/Hermes File Manager.app"

CHECK_BUNDLE=""
if [ -d "$RELEASE_BUNDLE" ]; then
    CHECK_BUNDLE="$RELEASE_BUNDLE"
    log_pass "Release Bundle 存在"
elif [ -d "$DEBUG_BUNDLE" ]; then
    CHECK_BUNDLE="$DEBUG_BUNDLE"
    log_pass "Debug Bundle 存在"
else
    log_warn "Bundle 未构建 (跳过 Bundle 验证)"
fi

if [ -n "$CHECK_BUNDLE" ]; then
    RESOURCES="$CHECK_BUNDLE/Contents/Resources"

    # 验证 Tauri 2.x 结构 (vue.html + assets/)
    VUE_PATH="$RESOURCES/vue.html"
    if [ -f "$VUE_PATH" ]; then
        SIZE=$(stat -f%z "$VUE_PATH" 2>/dev/null || stat -c%s "$VUE_PATH" 2>/dev/null)
        log_pass "Bundle 结构正确: vue.html (${SIZE} bytes)"
    else
        log_fail "Bundle 结构错误: vue.html 不存在"
        ls -la "$RESOURCES/" 2>/dev/null | head -10 || true
    fi
fi

echo ""

# ============================================================================
# 验证 4: CSP 配置安全 (HIST-015)
# ============================================================================
echo "【验证 4/5】CSP 配置安全 (HIST-015)"

CSP_FILE="$TAURI_DIR/tauri.conf.json"
if [ -f "$CSP_FILE" ]; then
    # 检查是否包含 unsafe-eval
    if grep -q 'unsafe-eval' "$CSP_FILE"; then
        log_fail "CSP 包含 unsafe-eval (安全风险)"
    else
        log_pass "CSP 不含 unsafe-eval"
    fi

    # 检查是否正确配置了 connect-src
    if grep -q "connect-src.*localhost" "$CSP_FILE"; then
        log_pass "CSP 配置了 localhost 连接"
    else
        log_warn "CSP 可能缺少 localhost 连接配置"
    fi
else
    log_fail "tauri.conf.json 不存在"
fi

echo ""

# ============================================================================
# 验证 5: 窗口 URL 配置正确 (G8)
# ============================================================================
echo "【验证 5/5】窗口 URL 配置 (G8)"

if [ -f "$CSP_FILE" ]; then
    # 检查主窗口 URL 配置
    if grep -q '../Resources/_up_/web/dist/app.html' "$CSP_FILE"; then
        log_pass "主窗口 URL 使用 Resources 相对路径"
    elif grep -q '_up_/web/dist/app.html' "$CSP_FILE"; then
        log_pass "主窗口 URL 使用 _up_ 结构"
    elif grep -q 'app.html' "$CSP_FILE"; then
        URL=$(grep -o '"url": *"[^"]*"' "$CSP_FILE" | head -1)
        log_warn "主窗口 URL 配置: $URL"
    fi

    # 检查浮窗 URL 配置
    if grep -q 'floating' "$CSP_FILE"; then
        log_pass "浮窗 URL 配置存在"
    fi
fi

echo ""

# ============================================================================
# 汇总报告
# ============================================================================
echo "============================================"
echo "验证汇总"
echo "============================================"
echo -e "${GREEN}通过: $PASS${NC}"
echo -e "${RED}失败: $FAIL${NC}"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}所有验证通过!${NC}"
    exit 0
else
    echo -e "${RED}存在 $FAIL 项验证失败，请检查构建配置${NC}"
    exit 1
fi