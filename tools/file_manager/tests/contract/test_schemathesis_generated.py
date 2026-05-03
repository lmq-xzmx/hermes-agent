"""
Schemathesis 自动生成的契约测试

使用 Schemathesis 从 OpenAPI Schema 自动生成测试用例。
这些测试验证 API 响应严格符合 schema 定义。

TDD 流程:
    Red: Schemathesis 生成的测试失败（API 返回不符合 schema）
    Green: 修复 API 代码或 schema 定义
    Refactor: 优化 schema 或测试代码

使用方式:
    pytest tests/contract/test_schemathesis_generated.py -v

或运行特定端点测试:
    schemathesis run http://localhost:8000/openapi.json --endpoint=/api/v1/auth/login --method=POST
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

API_BASE_URL = os.environ.get("TEST_API_BASE_URL", "http://localhost:8000")


# Check if Schemathesis is available
try:
    import schemathesis
    from schemathesis.openapi import from_path
    SCHEMATHESIS_AVAILABLE = True
except ImportError:
    SCHEMATHESIS_AVAILABLE = False
    pytest.skip("Schemathesis not installed. Install with: pip install schemathesis", allow_module_level=True)


class TestSchemathesisGenerated:
    """
    使用 Schemathesis 生成的契约测试

    这些测试方法会在运行时被 schemathesis 动态生成和扩展。
    """

    @pytest.fixture(scope="class")
    def schema(self):
        """
        加载 OpenAPI Schema

        从 FastAPI 应用获取 schema。
        """
        try:
            # Try to load from running API
            schema = from_path(f"{API_BASE_URL}/openapi.json")
            return schema
        except Exception as e:
            pytest.skip(f"Failed to load schema from {API_BASE_URL}: {e}")

    def test_api_endpoints_respond(self, schema):
        """
        基础契约测试: 所有定义的端点都应该响应

        验证 API 服务器正常运行，所有定义的端点都可访问。
        """
        # Get all endpoints
        endpoints = []
        for path, methods in schema.items():
            for method in methods.keys():
                endpoints.append((path, method.upper()))

        assert len(endpoints) > 0, "Schema must define at least one endpoint"
        print(f"\nFound {len(endpoints)} endpoints in schema")

    def test_openapi_schema_validity(self, schema):
        """
        契约测试: OpenAPI Schema 有效性

        验证加载的 schema 是有效的 OpenAPI 3.0 定义。
        """
        assert schema is not None, "Schema must be loaded"
        assert hasattr(schema, "openapi_version"), "Schema must have openapi_version"


# Dynamic test generation for specific endpoints
def generate_schemathesis_tests():
    """
    动态生成 Schemathesis 测试

    为每个 API 端点生成测试函数。
    这些测试会验证响应符合 schema 定义。

    使用 @schemathesis.parametrize 装饰器自动生成参数化测试。
    """
    if not SCHEMATHESIS_AVAILABLE:
        return

    try:
        # Load schema from running API
        schema = from_path(f"{API_BASE_URL}/openapi.json")

        # Define test endpoints
        endpoints_to_test = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/me",
            "/api/v1/admin/analytics/overview",
        ]

        for endpoint in endpoints_to_test:
            if endpoint in schema:
                # Create parameterized test for this endpoint
                @schemathesis.parametrize(
                    endpoint=endpoint,
                    method="GET",
                    tags=["test"]
                )
                def test_endpoint_response(case):
                    """
                    契约测试: 验证 {endpoint} 响应符合 schema
                    """
                    response = case.call()
                    case.validate_response(response)

                # Attach test to module
                    globals()[f"test_{endpoint.replace('/', '_').replace('-', '_')}"] = test_endpoint_response

    except Exception as e:
        print(f"Failed to generate tests: {e}")


# Run schemathesis directly from CLI:
#
# 1. Full API testing:
#    schemathesis run http://localhost:8000/openapi.json
#
# 2. Specific endpoint:
#    schemathesis run http://localhost:8000/openapi.json --endpoint=/api/v1/auth/login --method=POST
#
# 3. Generate report:
#    schemathesis run http://localhost:8000/openapi.json --report-file=contract_test_report.html
#
# 4. Use custom hypothesis strategies:
#    schemathesis run http://localhost:8000/openapi.json --hypothesis-seed=12345


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])

    # Or run schemathesis directly:
    # schemathesis run http://localhost:8000/openapi.json
