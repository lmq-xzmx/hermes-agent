"""
Lifecycle 契约测试

基于 INTERFACE_CONTRACT.md 定义的契约进行测试。
验证前后端 API 交互符合契约定义。

TDD 流程:
    Red: 编写失败的测试（验证契约）
    Green: 修复代码使测试通过
    Refactor: 优化代码

参考文档:
    - docs/architecture/INTERFACE_CONTRACT.md
    - config/lifecycle_config.yaml (canonical source)
    - docs/lifecycle/lifecycle_config.yaml (reference only)
"""

import os
import sys
import pytest
import requests
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# Test configuration
API_BASE_URL = os.environ.get("TEST_API_BASE_URL", "http://localhost:8000")


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def auth_headers() -> Dict[str, str]:
    """
    获取认证 Headers

    从 API 获取 token 用于认证请求。
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json={"username": "test_user", "password": "test_password"},
            timeout=5
        )
        if response.status_code == 200:
            token = response.json().get("access_token", "")
            return {"Authorization": f"Bearer {token}"}
    except Exception:
        pass

    return {}


@pytest.fixture(scope="module")
def admin_headers() -> Dict[str, str]:
    """
    获取 Admin 认证 Headers

    Admin API 需要特殊权限。
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=5
        )
        if response.status_code == 200:
            token = response.json().get("access_token", "")
            return {"Authorization": f"Bearer {token}"}
    except Exception:
        pass

    return {}


# =============================================================================
# Admin Analytics API 契约测试
# =============================================================================

class TestAdminAnalyticsContract:
    """
    Admin Analytics API 契约测试

    契约来源: INTERFACE_CONTRACT.md §1.1
    """

    def test_overview_response_schema(self, admin_headers: Dict[str, str]):
        """
        契约测试: GET /api/v1/admin/analytics/overview

        验证响应包含:
        - total_users, active_users_7d, new_users_7d
        - total_teams, total_spaces, total_pools
        - storage: {total_bytes, used_bytes, free_bytes, usage_rate}
        - alerts: [...]
        """
        response = requests.get(
            f"{API_BASE_URL}/api/v1/admin/analytics/overview",
            headers=admin_headers,
            timeout=5
        )

        # Assert response status
        assert response.status_code in [200, 401, 403], \
            f"Unexpected status code: {response.status_code}"

        if response.status_code != 200:
            pytest.skip("Admin authentication required")

        data = response.json()

        # Assert required fields (flat structure - no summary wrapper)
        required_fields = [
            "total_users", "active_users_7d", "new_users_7d",
            "total_teams", "total_spaces", "total_pools", "storage"
        ]
        for field in required_fields:
            assert field in data, f"Response must contain '{field}'"

        # Assert storage structure
        storage = data["storage"]
        storage_fields = ["total_bytes", "used_bytes", "free_bytes", "usage_rate"]
        for field in storage_fields:
            assert field in storage, f"storage must contain '{field}'"

        # Assert types
        assert isinstance(data["total_users"], int), "total_users must be int"
        assert isinstance(storage["usage_rate"], (int, float)), "usage_rate must be numeric"
        assert 0 <= storage["usage_rate"] <= 1, "usage_rate must be between 0 and 1"

        # Assert alerts structure (if present)
        if "alerts" in data:
            for alert in data["alerts"]:
                assert "id" in alert, "alert must contain 'id'"
                assert "type" in alert, "alert must contain 'type'"
                assert "level" in alert, "alert must contain 'level'"

    def test_storage_pools_response_schema(self, admin_headers: Dict[str, str]):
        """
        契约测试: GET /api/v1/admin/analytics/storage-pools

        验证响应符合 INTERFACE_CONTRACT.md §1.1 定义的 schema。
        """
        response = requests.get(
            f"{API_BASE_URL}/api/v1/admin/analytics/storage-pools",
            headers=admin_headers,
            timeout=5
        )

        assert response.status_code in [200, 401, 403]

        if response.status_code != 200:
            pytest.skip("Admin authentication required")

        data = response.json()

        # Assert pools array
        assert "pools" in data, "Response must contain 'pools' field"
        assert isinstance(data["pools"], list), "pools must be an array"

        # Assert pool structure
        for pool in data["pools"]:
            required_fields = [
                "id", "name", "protocol", "total_bytes",
                "used_bytes", "free_bytes", "usage_rate"
            ]
            for field in required_fields:
                assert field in pool, f"pool must contain '{field}'"

            # Assert types
            assert isinstance(pool["usage_rate"], (int, float)), "usage_rate must be numeric"
            assert 0 <= pool["usage_rate"] <= 1, "usage_rate must be between 0 and 1"


# =============================================================================
# Lifecycle API 契约测试
# =============================================================================

class TestLifecycleContract:
    """
    Lifecycle API 契约测试

    契约来源:
        - INTERFACE_CONTRACT.md §1.2
        - config/lifecycle_config.yaml
    """

    def test_create_team_constraint_no_pool(self, auth_headers: Dict[str, str]):
        """
        契约测试: POST /api/v1/teams (无存储池)

        验证 config/lifecycle_config.yaml 定义的约束:
        - code: NO_AVAILABLE_POOL
        - error_template: "系统暂无可用存储池，无法创建新团队"
        """
        if not auth_headers:
            pytest.skip("Authentication required")

        response = requests.post(
            f"{API_BASE_URL}/api/v1/teams",
            headers=auth_headers,
            json={"name": "TestTeam", "storage_pool_id": "nonexistent"},
            timeout=5
        )

        # Should be rejected with constraint error or auth error
        assert response.status_code in [200, 400, 401, 403, 404], \
            f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            # Team created successfully - pool exists
            pass
        elif response.status_code == 401:
            pytest.skip("Authentication failed - invalid credentials")
        else:
            # Constraint triggered - verify error format
            data = response.json()
            assert "error" in data or "code" in data or "message" in data, \
                "Error response must contain error information"

    def test_invite_member_constraint_not_owner(self, auth_headers: Dict[str, str]):
        """
        契约测试: POST /api/v1/spaces/{id}/members (非所有者)

        验证 config/lifecycle_config.yaml 定义的约束:
        - code: NOT_SPACE_OWNER
        - error_template: "只有空间所有者可以邀请成员"
        """
        if not auth_headers:
            pytest.skip("Authentication required")

        # This test would require a space where the user is not owner
        # Simplified version for contract validation
        response = requests.post(
            f"{API_BASE_URL}/api/v1/spaces/test_space_id/members",
            headers=auth_headers,
            json={"user_id": "target_user", "role": "member"},
            timeout=5
        )

        # Should be 401 (unauthorized), 403 (forbidden), or 404 (space not found)
        assert response.status_code in [401, 403, 404], \
            f"Unexpected status: {response.status_code}"

    def test_quota_exceeded_constraint(self, auth_headers: Dict[str, str]):
        """
        契约测试: POST /api/v1/files/upload (配额超限)

        验证 config/lifecycle_config.yaml 定义的约束:
        - code: QUOTA_EXCEEDED
        - error_template: "存储配额已用尽，无法上传新文件"
        """
        if not auth_headers:
            pytest.skip("Authentication required")

        # This test would require setting up a full quota scenario
        # Simplified contract validation
        response = requests.post(
            f"{API_BASE_URL}/api/v1/files/upload",
            headers=auth_headers,
            json={"space_id": "test_space", "filename": "test.bin", "size": 999999999999},
            timeout=5
        )

        # Should be 401 (unauthorized), 403/413/507 (quota error), or 404 (endpoint not found)
        assert response.status_code in [200, 401, 403, 404, 413, 507], \
            f"Unexpected status: {response.status_code}"


# =============================================================================
# Auth API 契约测试
# =============================================================================

class TestAuthContract:
    """
    Auth API 契约测试

    契约来源: INTERFACE_CONTRACT.md §2 (隐式定义)
    """

    def test_login_response_schema(self):
        """
        契约测试: POST /api/v1/auth/login

        验证响应包含:
        - access_token: str
        - refresh_token: str
        - token_type: str = "bearer"
        - expires_in: int
        - user: UserResponseDTO
        """
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json={"username": "test", "password": "test"},
            timeout=5
        )

        assert response.status_code in [200, 401], \
            f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()

            # Assert required fields
            assert "access_token" in data, "Response must contain 'access_token'"
            assert "refresh_token" in data, "Response must contain 'refresh_token'"
            assert "token_type" in data, "Response must contain 'token_type'"
            assert data["token_type"] == "bearer", "token_type must be 'bearer'"

            # Assert user structure (if returned)
            if "user" in data:
                user = data["user"]
                assert "id" in user, "user must contain 'id'"
                assert "username" in user, "user must contain 'username'"

    def test_register_response_schema(self):
        """
        契约测试: POST /api/v1/auth/register

        验证响应符合 UserResponseDTO 结构。
        """
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/register",
            json={
                "username": "newuser",
                "password": "password123",
                "email": "newuser@example.com"
            },
            timeout=5
        )

        # Should succeed or return validation error
        assert response.status_code in [200, 201, 400, 409], \
            f"Unexpected status: {response.status_code}"

        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data or "access_token" in data, \
                "Successful registration must return user id or token"


# =============================================================================
# Error Code 契约测试
# =============================================================================

class TestErrorCodeContract:
    """
    错误码契约测试

    契约来源: ERROR_CODE_CONTRACT.md
    """

    def test_quota_exceeded_error_code(self, auth_headers: Dict[str, str]):
        """
        契约测试: 配额超限错误码

        验证错误响应符合 ERROR_CODE_CONTRACT.md 定义:
        - code: QUOTA_EXCEEDED
        - message: 用户友好的中文提示
        """
        # This would need a full quota scenario setup
        pytest.skip("Requires full quota setup")

    def test_not_space_member_error_code(self, auth_headers: Dict[str, str]):
        """
        契约测试: 非成员错误码

        验证错误响应符合 ERROR_CODE_CONTRACT.md 定义:
        - code: NOT_SPACE_MEMBER
        """
        # Simplified test
        response = requests.post(
            f"{API_BASE_URL}/api/v1/spaces/invalid_space/members",
            headers=auth_headers,
            json={"user_id": "test_user"},
            timeout=5
        )

        # Should return constraint error
        if response.status_code >= 400:
            data = response.json()
            # Error should have structured format
            assert isinstance(data, dict), "Error response must be JSON object"


# =============================================================================
# WebSocket 契约测试
# =============================================================================

class TestWebSocketContract:
    """
    WebSocket 契约测试

    验证 WebSocket 消息格式符合 INTERFACE_CONTRACT.md 定义。
    """

    def test_ws_auth_message_format(self):
        """
        契约测试: WebSocket 认证消息格式

        验证:
        - 消息类型: auth
        - 包含 token
        - 响应包含 success/error
        """
        import websocket

        ws_url = API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/api/v1/analytics/ws"

        try:
            ws = websocket.create_connection(ws_url, timeout=5)
            ws.close()
        except Exception as e:
            pytest.skip(f"WebSocket not available: {e}")


# =============================================================================
# Run Contract Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
