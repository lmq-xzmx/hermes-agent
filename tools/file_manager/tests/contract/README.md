# Contract Tests - 契约测试

> **任务**: T7 - 契约测试自动化
> **目标**: 100% API 契约覆盖率
> **工具**: Schemathesis + OpenAPI

---

## 概述

契约测试确保前后端 API 交互严格符合 OpenAPI Schema 定义。

### TDD 流程

```
Red (红)     →  编写失败的测试
   ↓
Green (绿)   →  修复代码使测试通过
   ↓
Refactor    →  优化代码
```

---

## 安装依赖

```bash
pip install schemathesis pytest requests websocket-client
```

---

## 运行测试

### 1. 基础契约测试

```bash
# 确保 API 运行在 localhost:8000
cd tools/file_manager
pytest tests/contract/ -v
```

### 2. 使用 Schemathesis CLI

```bash
# 完整 API 测试
schemathesis run http://localhost:8000/openapi.json

# 指定端点测试
schemathesis run http://localhost:8000/openapi.json \
    --endpoint=/api/v1/auth/login \
    --method=POST

# 生成 HTML 报告
schemathesis run http://localhost:8000/openapi.json \
    --report-file=contract_report.html
```

### 3. 运行特定测试

```bash
# 仅运行 Admin Analytics 契约测试
pytest tests/contract/test_lifecycle_contract.py::TestAdminAnalyticsContract -v

# 仅运行 Auth 契约测试
pytest tests/contract/test_lifecycle_contract.py::TestAuthContract -v
```

---

## 测试文件结构

```
tests/contract/
├── __init__.py                    # Package marker
├── conftest.py                    # Shared fixtures
├── pytest.ini                     # Pytest 配置
├── README.md                      # 本文件
├── test_lifecycle_contract.py      # 基于 INTERFACE_CONTRACT.md 的契约测试
└── test_schemathesis_generated.py # Schemathesis 自动生成测试
```

---

## 契约定义来源

| 文档 | 位置 | 用途 |
|------|------|------|
| INTERFACE_CONTRACT.md | docs/architecture/ | REST API 契约定义 |
| lifecycle_config.yaml | docs/architecture/ | Lifecycle 约束规则 |
| ERROR_CODE_CONTRACT.md | docs/architecture/ | 错误码契约 |

---

## 测试覆盖的 API

### Admin Analytics

| 端点 | 方法 | 测试状态 |
|------|------|---------|
| `/api/v1/admin/analytics/overview` | GET | ✅ |
| `/api/v1/admin/analytics/storage-pools` | GET | ✅ |

### Auth

| 端点 | 方法 | 测试状态 |
|------|------|---------|
| `/api/v1/auth/login` | POST | ✅ |
| `/api/v1/auth/register` | POST | ✅ |
| `/api/v1/auth/me` | GET | ✅ |

### Lifecycle

| 端点 | 方法 | 测试状态 |
|------|------|---------|
| `/api/v1/teams` | POST | ✅ |
| `/api/v1/spaces/{id}/members` | POST | ✅ |
| `/api/v1/files/upload` | POST | ✅ |

---

## Schemathesis 使用

### 生成测试用例

```python
import schemathesis
from schemathesis.specs.openapi import from_path

# 加载 schema
schema = from_path("http://localhost:8000/openapi.json")

# 生成测试用例
@schemathesis.parametrize(endpoint="/api/v1/auth/login", method="POST")
def test_login(case):
    response = case.call()
    case.validate_response(response)
```

### 自定义 Hypothesis 策略

```python
from hypothesis import strategies as st

@schemathesis.parametrize(
    endpoint="/api/v1/auth/register",
    method="POST",
    hypotheses_settings={"max_examples": 100}
)
def test_register_custom(case):
    response = case.call()
    case.validate_response(response)
```

---

## CI/CD 集成

### GitHub Actions

```yaml
name: Contract Tests

on: [push, pull_request]

jobs:
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install schemathesis pytest requests
      - name: Start API
        run: python server.py &
      - name: Run contract tests
        run: schemathesis run http://localhost:8000/openapi.json --report-file=report.html
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: contract-test-report
          path: report.html
```

---

## 故障排除

### API 未运行

```bash
# 启动 API
python server.py

# 验证运行
curl http://localhost:8000/health
```

### Schema 加载失败

```bash
# 检查 OpenAPI schema
curl http://localhost:8000/openapi.json | jq .
```

### 测试失败

1. 检查 API 响应是否符合 schema
2. 检查 schema 定义是否正确
3. 如果 schema 需要更新，修改 DTO 定义后重新生成

---

## 参考资料

- [Schemathesis 文档](https://schemathesis.readthedocs.io/)
- [OpenAPI 规范](https://swagger.io/specification/)
- [Pytest 文档](https://docs.pytest.org/)
