"""
Contract Test Configuration - Schemathesis + OpenAPI Schema

使用 Schemathesis 进行前后端契约测试：
1. 从 FastAPI /openapi.json 获取 schema
2. 使用 Schemathesis 生成测试用例
3. 验证 API 响应符合 schema 定义

TDD 流程:
    Red: 编写失败的测试（schema 验证失败）
    Green: 修复代码/配置使测试通过
    Refactor: 优化代码
"""

import os
import sys
import pytest
from typing import Generator

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Schemathesis import
try:
    import schemathesis
    from schemathesis.openapi import from_path
    SCHEMATHESIS_AVAILABLE = True
except ImportError:
    SCHEMATHESIS_AVAILABLE = False
    pytest.skip("Schemathesis not installed", allow_module_level=True)


# Test configuration
API_BASE_URL = os.environ.get("TEST_API_BASE_URL", "http://localhost:8000")
OPENAPI_SCHEMA_URL = f"{API_BASE_URL}/openapi.json"


@pytest.fixture(scope="module")
def openapi_schema() -> dict:
    """
    加载 OpenAPI Schema

    从 FastAPI 应用获取 OpenAPI schema 定义。
    如果 API 未运行，测试将被跳过。
    """
    import requests

    try:
        response = requests.get(OPENAPI_SCHEMA_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        pytest.skip(f"API not available at {API_BASE_URL}", allow_module_level=True)
    except requests.exceptions.HTTPError as e:
        pytest.skip(f"Failed to fetch OpenAPI schema: {e}", allow_module_level=True)


@pytest.fixture(scope="module")
def api_endpoints(openapi_schema: dict) -> list:
    """
    提取所有 API 端点

    返回格式:
        [
            {"path": "/api/v1/auth/login", "method": "POST", "tag": "auth"},
            ...
        ]
    """
    endpoints = []
    paths = openapi_schema.get("paths", {})

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                tags = details.get("tags", ["untagged"])
                endpoints.append({
                    "path": path,
                    "method": method.upper(),
                    "tag": tags[0] if tags else "untagged",
                    "summary": details.get("summary", ""),
                })

    return endpoints


@pytest.fixture(scope="module")
def auth_token(openapi_schema: dict) -> str:
    """
    获取认证 Token

    用于需要认证的 API 端点测试。
    """
    import requests

    # Try to get token via login endpoint
    # This is a placeholder - in real tests, you'd use test credentials
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json={"username": "test_user", "password": "test_password"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("access_token", "")
    except Exception:
        pass

    return ""


class ContractTestRunner:
    """
    契约测试运行器

    使用 Schemathesis 的 hypothesis 策略生成测试用例。
    """

    def __init__(self, schema_url: str):
        self.schema_url = schema_url
        self.api_schema = None

    def load_schema(self):
        """加载 OpenAPI Schema"""
        if not SCHEMATHESIS_AVAILABLE:
            raise RuntimeError("Schemathesis not installed")

        # Load schema from URL
        self.api_schema = from_path(self.schema_url)
        return self.api_schema

    def generate_testcases(self, endpoint_path: str, method: str = "GET"):
        """为指定端点生成测试用例"""
        if not self.api_schema:
            self.load_schema()

        # Get endpoint schema
        endpoint = self.api_schema[endpoint_path][method]

        # Generate hypothesis strategy
        strategy = endpoint.as_strategy()

        return strategy


# Pytest collection hook
def pytest_configure(config):
    """Pytest 配置"""
    config.addinivalue_line(
        "markers", "contract: mark test as a contract test"
    )
    config.addinivalue_line(
        "markers", "openapi: mark test as OpenAPI schema test"
    )


def pytest_collection_modifyitems(items):
    """自动标记契约测试"""
    for item in items:
        if "contract" in item.nodeid or "schemathesis" in str(item.fspath):
            item.add_marker(pytest.mark.contract)
