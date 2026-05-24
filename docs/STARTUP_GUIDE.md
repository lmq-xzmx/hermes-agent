# Hermes Agent 启动指南

## 子模块概览

| 模块 | 路径 | 技术栈 | 端口 | 启动命令 |
|------|------|--------|------|----------|
| **Hermes File Manager** | `tools/file_manager/` | Python/FastAPI | 8080 | `python3 server.py` |
| **hermes-mcp** | `tools/claudian_hermes_plugin/` | Node.js/TypeScript | MCP | `npm run build` |
| **LLM Wiki FM** | `llm_wiki_FM/` | Rust/Tauri | 19827 | 编译后启动 |

---

## 快速启动

### 方式一：独立启动

```bash
# 1. Hermes File Manager (API + Web UI)
cd tools/file_manager
python3 server.py

# 2. hermes-mcp (需要单独终端)
cd tools/claudian_hermes_plugin
npm install
npm run build

# 3. LLM Wiki FM (需要先编译)
cd llm_wiki_FM
cargo build --release
open -a "src-tauri/target/release/bundle/macos/LLM Wiki FM.app"
```

### 方式二：使用 start_services.sh

部署后会自动在项目根目录生成 `start_services.sh`：

```bash
./start_services.sh   # 启动所有服务
./stop_services.sh   # 停止所有服务
```

---

## 前置要求

### 所有平台

- Python 3.11+
- Node.js 18+
- Git

### macOS/Linux

- Rust 1.93.0+
- CMake (用于 LLM Wiki 编译)

---

## 服务地址

| 服务 | URL |
|------|-----|
| Hermes File Manager Web UI | http://localhost:8080 |
| Hermes File Manager API | http://localhost:8080/api/v1 |
| LLM Wiki | http://localhost:19827 |
| LLM Wiki 健康检查 | http://localhost:19827/health |

---

## Intel Mac 注意事项

1. **编译优化**：Intel Mac 可使用更多 CPU 核心并行编译：
   ```bash
   CARGO_BUILD_JOBS=$(sysctl -n hw.ncpu) cargo build --release
   ```

2. **架构兼容性**：所有 Python/Node.js 组件无架构限制；Rust 组件需重新编译。

3. **端口冲突**：如果 8080/19827 被占用：
   ```bash
   lsof -i :8080    # 查看占用进程
   kill -9 <PID>    # 终止进程
   ```

---

## 故障排除

### Python 模块找不到
```bash
cd tools/file_manager
source venv/bin/activate  # 或手动创建: python3 -m venv venv
pip install -e .
```

### Node 模块安装失败
```bash
cd tools/claudian_hermes_plugin
rm -rf node_modules package-lock.json
npm install
```

### LLM Wiki 编译失败
```bash
cd llm_wiki_FM
cargo clean
cargo build --release 2>&1 | tail -50
```