# T8 性能基准测试

> **版本**: 1.0
> **创建日期**: 2026-05-06
> **参考规范**: DESIGN.md (Apple Design System)

---

## 性能目标

| 指标 | 阈值 | 说明 |
|------|------|------|
| API P95 延迟 | < 150ms | 关键 API 端点 |
| WebSocket 延迟 | < 100ms | 实时通信 |
| 页面加载时间 | < 3s | 首次加载 |
| 并发用户 | 100+ | 峰值负载 |
| 内存增长 | < 10%/小时 | 稳定性 |

---

## 测试结构

```
tests/benchmark/
├── conftest.py              # 共享 fixtures
├── pytest.ini               # pytest 配置
├── test_api_latency.py      # API 延迟测试
├── test_websocket_latency.py # WebSocket 延迟测试
├── test_stability.py         # 稳定性测试
├── locustfile.py             # Locust 负载测试
└── scripts/
    └── run_benchmarks.py     # 测试运行脚本
```

---

## 快速运行

### 1. API 延迟测试

```bash
# 运行 API 基准测试
python -m pytest tests/benchmark/ -v -m benchmark

# 仅运行快速测试（跳过长时间测试）
python -m pytest tests/benchmark/ -v -m "benchmark and not slow"

# 运行单个测试
python -m pytest tests/benchmark/test_api_latency.py::TestAPILatency::test_health_endpoint_latency -v
```

### 2. WebSocket 延迟测试

```bash
# 运行 WebSocket 模拟测试
python -m pytest tests/benchmark/test_websocket_latency.py::TestWebSocketSimulated -v

# 注意: 真实 WebSocket 测试需要运行服务器
```

### 3. 稳定性测试

```bash
# 运行稳定性测试 (需要几分钟)
python -m pytest tests/benchmark/test_stability.py -v

# 跳过长时间测试
python -m pytest tests/benchmark/test_stability.py -v -m "stability and not slow"
```

### 4. Locust 负载测试

```bash
# 安装 Locust
pip install locust

# 运行 Locust Web UI
cd tools/file_manager
locust -f tests/benchmark/locustfile.py --host=http://localhost:8080

# Headless 模式运行
locust -f tests/benchmark/locustfile.py \
    --host=http://localhost:8080 \
    --users=100 \
    --spawn-rate=10 \
    --run-time=60s \
    --headless \
    --csv=reports/locust
```

### 5. 使用测试脚本

```bash
# 运行所有快速测试
python tests/benchmark/scripts/run_benchmarks.py --type api

# 运行特定类型
python tests/benchmark/scripts/run_benchmarks.py --type ws
python tests/benchmark/scripts/run_benchmarks.py --type stability
python tests/benchmark/scripts/run_benchmarks.py --type load

# 运行全部测试
python tests/benchmark/scripts/run_benchmarks.py --all
```

---

## 测试类型

### @pytest.mark.benchmark
API 和 WebSocket 延迟测试，验证性能阈值。

### @pytest.mark.stability
内存、CPU、线程稳定性测试。

### @pytest.mark.integration
需要运行服务器的集成测试。

---

## 性能指标

### API 延迟测试结果

| 测试 | 状态 | 说明 |
|------|------|------|
| test_health_endpoint_latency | ✅ PASS | P95 < 50ms |
| test_system_status_latency | ✅ PASS | P95 < 100ms |
| test_api_latency_simulated | ✅ PASS | 模拟测试 |

### WebSocket 延迟测试

| 测试 | 状态 | 说明 |
|------|------|------|
| test_ws_latency_simulation | ✅ PASS | 模拟测试 |

### 稳定性测试

| 测试 | 状态 | 说明 |
|------|------|------|
| test_memory_stability_short | ✅ PASS | 60秒内存稳定性 |
| test_cpu_stability | ✅ PASS | CPU 使用率验证 |

---

## 集成测试 (需要服务器)

以下测试需要运行中的服务器:

- `test_admin_overview_latency` - 需要 /api/v1/admin/analytics/overview
- `test_list_users_latency` - 需要 /api/v1/admin/users
- `test_list_spaces_latency` - 需要 /api/v1/spaces
- `test_storage_pools_latency` - 需要 /api/v1/pools

启动服务器后运行:

```bash
python -m pytest tests/benchmark/ -v -m integration
```

---

## 性能基准目标 (来自 DESIGN.md)

根据 DESIGN.md:

> **性能基准**:
> - API 响应时间: <200ms (p95)
> - 页面加载时间: <3s
> - WebSocket 延迟: <100ms

---

## 添加新测试

### 添加新的 API 延迟测试

```python
@pytest.mark.benchmark
def test_new_endpoint_latency(self, bench_api_client, benchmark_config):
    """Test new endpoint latency."""
    latencies = []
    for _ in range(100):
        result = measure_latency(bench_api_client, "GET", "/api/v1/new-endpoint")
        latencies.append(result.latency_ms)

    assert_latency_threshold("GET /api/v1/new-endpoint", latencies, 100.0)
```

### 添加新的负载测试

```python
@task(5)
def new_load_task(self):
    """New load test task."""
    if self.token:
        self.client.get("/api/v1/new-endpoint", headers=self.headers)
```
